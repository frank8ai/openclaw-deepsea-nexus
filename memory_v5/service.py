from __future__ import annotations

import json
import os
import threading
import queue
import uuid
import hashlib
from datetime import datetime, timezone
from math import log1p
from typing import Any, Dict, List, Optional, Tuple

from .models import MemoryScope, MemoryResource, MemoryItem, MemoryCategory, MemoryEdge, MemoryHit, now_iso
from .layout import MemoryLayout
from .index import MemoryIndex

try:
    from runtime_paths import resolve_memory_root
except ImportError:
    from ..runtime_paths import resolve_memory_root

try:
    from context_contract import normalize_typed_context, sanitize_typed_context_for_durable_write
except ImportError:
    from ..context_contract import normalize_typed_context, sanitize_typed_context_for_durable_write


def _uuid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _clean_list(items: Optional[List[str]]) -> List[str]:
    if not items:
        return []
    out = []
    for it in items:
        if not it:
            continue
        val = str(it).strip()
        if not val:
            continue
        out.append(val)
    return out


def _safe_str(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _default_scope(config: Dict[str, Any]) -> MemoryScope:
    mem_cfg = config.get("memory_v5", {}) if isinstance(config, dict) else {}
    scope_cfg = mem_cfg.get("scope", {}) if isinstance(mem_cfg.get("scope", {}), dict) else {}
    session_key = os.environ.get("OPENCLAW_SESSION_KEY") or os.environ.get("CODEX_SESSION_KEY") or ""
    agent_hint = os.environ.get("OPENCLAW_AGENT_NAME") or os.environ.get("OPENCLAW_AGENT_ID") or ""
    if not agent_hint and session_key.startswith("agent:"):
        parts = session_key.split(":")
        if len(parts) > 1:
            agent_hint = parts[1]
    agent_cfg = (scope_cfg.get("agent_id") or "").strip()
    if agent_cfg.lower() == "auto" or agent_cfg == "":
        if not agent_hint:
            cwd = os.getcwd()
            if "workspace-" in cwd:
                agent_hint = cwd.split("workspace-", 1)[1].split(os.sep, 1)[0]
            elif cwd.rstrip(os.sep).endswith("workspace"):
                agent_hint = "main"
        agent_cfg = agent_hint or "default"
    return MemoryScope(
        agent_id=agent_cfg or os.environ.get("NEXUS_AGENT_ID") or agent_hint or "default",
        user_id=scope_cfg.get("user_id") or os.environ.get("NEXUS_USER_ID") or os.environ.get("OPENCLAW_USER_ID") or os.environ.get("CODEX_USER_ID") or "default",
        run_id=scope_cfg.get("run_id") or "",
        app_id=scope_cfg.get("app_id") or "",
        workspace=scope_cfg.get("workspace") or "",
    )


def _resolve_root(config: Dict[str, Any]) -> str:
    return resolve_memory_root(config, default_base=os.getcwd())


class MemoryV5Service:
    def __init__(self, config: Dict[str, Any]):
        self.config = config if isinstance(config, dict) else {}
        mem_cfg = self.config.get("memory_v5", {}) if isinstance(self.config, dict) else {}
        self.enabled = bool(mem_cfg.get("enabled", True))
        self.async_ingest = bool(mem_cfg.get("async_ingest", True))
        self.graph_enabled = bool(mem_cfg.get("graph_enabled", True))
        self.category_max_items = max(10, int(mem_cfg.get("category_max_items", 50)))
        self.fts_enabled = bool(mem_cfg.get("fts_enabled", True))
        self.ttl_days_default = int(mem_cfg.get("ttl_days_default", 0))
        self.decay_half_life_days_default = int(mem_cfg.get("decay_half_life_days", 30))
        self.archive_after_days = int(mem_cfg.get("archive_after_days", 180))
        self.usage_boost = float(mem_cfg.get("usage_boost", 0.08))
        self.item_kind_defaults = self._normalize_item_kind_defaults(mem_cfg.get("item_kind_defaults"))
        self.root = _resolve_root(self.config)
        self.scope = _default_scope(self.config)
        self._storage_lock = threading.Lock()
        self._layouts: Dict[str, MemoryLayout] = {}
        self._indexes: Dict[str, MemoryIndex] = {}
        # Backward-compatible attributes for default scope.
        self.layout, self.index = self._ensure_scope_storage(self.scope)
        self._queue: "queue.Queue[tuple]" = queue.Queue()
        self._worker: Optional[threading.Thread] = None
        if self.enabled and self.async_ingest:
            self._start_worker()

    def _start_worker(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    def _normalize_item_kind_defaults(self, payload: Any) -> Dict[str, Dict[str, int]]:
        if not isinstance(payload, dict):
            return {}
        normalized: Dict[str, Dict[str, int]] = {}
        for kind, raw in payload.items():
            key = _safe_str(kind).lower()
            if not key or not isinstance(raw, dict):
                continue
            entry: Dict[str, int] = {}
            if "ttl_days" in raw:
                entry["ttl_days"] = max(0, _safe_int(raw.get("ttl_days"), self.ttl_days_default))
            if "decay_half_life_days" in raw:
                entry["decay_half_life_days"] = max(
                    0,
                    _safe_int(raw.get("decay_half_life_days"), self.decay_half_life_days_default),
                )
            if "archive_after_days" in raw:
                entry["archive_after_days"] = max(
                    0,
                    _safe_int(raw.get("archive_after_days"), self.archive_after_days),
                )
            if entry:
                normalized[key] = entry
        return normalized

    def _worker_loop(self) -> None:
        while True:
            try:
                payload = self._queue.get()
                if payload is None:
                    return
                action, args, kwargs = payload
                if action == "summary":
                    self._ingest_summary(*args, **kwargs)
                elif action == "document":
                    self._ingest_document(*args, **kwargs)
            except Exception:
                continue

    def _write_json(self, path: str, payload: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False, indent=2))

    def _normalize_scope(self, scope: Optional[MemoryScope]) -> MemoryScope:
        return (scope or self.scope).normalized()

    def _ensure_scope_storage(self, scope: MemoryScope) -> Tuple[MemoryLayout, MemoryIndex]:
        scope = scope.normalized()
        key = scope.scope_key()
        with self._storage_lock:
            layout = self._layouts.get(key)
            if layout is None:
                layout = MemoryLayout(self.root, scope)
                layout.ensure_dirs()
                self._layouts[key] = layout
            index = self._indexes.get(key)
            if index is None:
                index = MemoryIndex(layout.index_path(), fts_enabled=self.fts_enabled)
                self._indexes[key] = index
        return layout, index

    def _resolve_item_lifecycle_defaults(self, kind: str) -> Dict[str, int]:
        resolved = {
            "ttl_days": max(0, _safe_int(self.ttl_days_default, 0)),
            "decay_half_life_days": max(0, _safe_int(self.decay_half_life_days_default, 0)),
            "archive_after_days": max(0, _safe_int(self.archive_after_days, 0)),
        }
        for key in ("default", _safe_str(kind).lower()):
            override = self.item_kind_defaults.get(key)
            if not override:
                continue
            if "ttl_days" in override:
                resolved["ttl_days"] = max(0, _safe_int(override.get("ttl_days"), resolved["ttl_days"]))
            if "decay_half_life_days" in override:
                resolved["decay_half_life_days"] = max(
                    0,
                    _safe_int(override.get("decay_half_life_days"), resolved["decay_half_life_days"]),
                )
            if "archive_after_days" in override:
                resolved["archive_after_days"] = max(
                    0,
                    _safe_int(override.get("archive_after_days"), resolved["archive_after_days"]),
                )
        return resolved

    def _resolve_now(self, now_ts: Optional[Any] = None) -> datetime:
        if isinstance(now_ts, datetime):
            current = now_ts
        else:
            raw = _safe_str(now_ts)
            if not raw:
                return datetime.now(timezone.utc)
            try:
                current = datetime.fromisoformat(raw)
            except Exception:
                return datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        return current

    def _item_age_days(self, row: Dict[str, Any], now_ts: Optional[Any] = None) -> float:
        now = self._resolve_now(now_ts)
        updated_at = row.get("updated_at") or row.get("created_at")
        if not updated_at:
            return 0.0
        try:
            ts = datetime.fromisoformat(str(updated_at))
        except Exception:
            return 0.0
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return max(0.0, (now - ts).total_seconds() / 86400.0)

    def _item_lifecycle_state(self, row: Dict[str, Any], now_ts: Optional[Any] = None) -> Dict[str, Any]:
        age_days = self._item_age_days(row, now_ts)
        archived = bool(_safe_int(row.get("archived"), 0))
        ttl_days = _safe_int(row.get("ttl_days"), 0)
        half_life = _safe_int(
            row.get("decay_half_life_days"),
            _safe_int(self.decay_half_life_days_default, 0),
        )
        archive_after_days = _safe_int(
            row.get("archive_after_days"),
            _safe_int(self.archive_after_days, 0),
        )
        decay_multiplier = 1.0
        if half_life > 0 and age_days > 0:
            decay_multiplier = 0.5 ** (age_days / float(half_life))
        ttl_expired = ttl_days > 0 and age_days > float(ttl_days)
        archive_due = (not archived) and archive_after_days > 0 and age_days > float(archive_after_days)
        return {
            "age_days": age_days,
            "archived": archived,
            "ttl_days": ttl_days,
            "ttl_expired": ttl_expired,
            "decay_half_life_days": half_life,
            "decay_multiplier": decay_multiplier,
            "archive_after_days": archive_after_days,
            "archive_due": archive_due,
        }

    def _lifecycle_scope_payload(self, scope: MemoryScope) -> Dict[str, str]:
        return {
            "agent_id": scope.agent_id,
            "user_id": scope.user_id,
            "app_id": scope.app_id,
            "run_id": scope.run_id,
            "workspace": scope.workspace,
        }

    def _lifecycle_sample_payload(self, row: Dict[str, Any], lifecycle: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": str(row.get("id", "")),
            "title": str(row.get("title", "")),
            "kind": str(row.get("kind", "note")),
            "category": str(row.get("category", "")),
            "source_id": str(row.get("source_id", "")),
            "age_days": round(float(lifecycle.get("age_days", 0.0)), 3),
            "ttl_days": _safe_int(lifecycle.get("ttl_days"), 0),
            "decay_half_life_days": _safe_int(lifecycle.get("decay_half_life_days"), 0),
            "archive_after_days": _safe_int(lifecycle.get("archive_after_days"), 0),
            "decay_multiplier": round(float(lifecycle.get("decay_multiplier", 1.0)), 6),
            "archived": bool(lifecycle.get("archived", False)),
            "ttl_expired": bool(lifecycle.get("ttl_expired", False)),
            "archive_due": bool(lifecycle.get("archive_due", False)),
        }

    def _archive_backfill_candidate_payload(
        self,
        row: Dict[str, Any],
        lifecycle: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        if lifecycle.get("archived"):
            return None
        current_archive_after_days = _safe_int(row.get("archive_after_days"), 0)
        if current_archive_after_days > 0:
            return None
        resolved_archive_after_days = _safe_int(
            self._resolve_item_lifecycle_defaults(str(row.get("kind", "note"))).get("archive_after_days"),
            0,
        )
        if resolved_archive_after_days <= 0:
            return None
        return {
            "id": str(row.get("id", "")),
            "title": str(row.get("title", "")),
            "kind": str(row.get("kind", "note")),
            "category": str(row.get("category", "")),
            "source_id": str(row.get("source_id", "")),
            "age_days": round(float(lifecycle.get("age_days", 0.0)), 3),
            "current_archive_after_days": current_archive_after_days,
            "resolved_archive_after_days": resolved_archive_after_days,
        }

    def _load_lifecycle_rows(
        self,
        scope: MemoryScope,
        now_ts: Optional[Any] = None,
    ) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        _, index = self._ensure_scope_storage(scope)
        rows = index.list_all_items(scope, include_archived=True)
        return [(row, self._item_lifecycle_state(row, now_ts)) for row in rows]

    def _build_item(
        self,
        *,
        kind: str,
        title: str,
        content: str,
        tags: Optional[List[str]],
        keywords: Optional[List[str]],
        entities: Optional[List[str]],
        project: str,
        category: str,
        source_id: str,
        confidence: str,
        scope: MemoryScope,
    ) -> MemoryItem:
        lifecycle = self._resolve_item_lifecycle_defaults(kind)
        return MemoryItem(
            id=_uuid("item"),
            title=_safe_str(title) or "Untitled",
            content=_safe_str(content),
            kind=kind,
            tags=_clean_list(tags),
            keywords=_clean_list(keywords),
            entities=_clean_list(entities),
            project=project,
            category=category,
            source_id=source_id,
            confidence=_safe_str(confidence) or "medium",
            ttl_days=lifecycle["ttl_days"],
            decay_half_life_days=lifecycle["decay_half_life_days"],
            archive_after_days=lifecycle["archive_after_days"],
            scope=scope,
        )

    def ingest_summary(
        self,
        conversation_id: str,
        reply: str,
        summary: Optional[Dict[str, Any]],
        user_query: str = "",
        scope: Optional[MemoryScope] = None,
    ) -> Dict[str, Any]:
        if not self.enabled:
            return {"enabled": False, "stored": 0}
        if self.async_ingest:
            self._queue.put(("summary", (conversation_id, reply, summary, user_query, scope), {}))
            return {"enabled": True, "queued": True}
        return self._ingest_summary(conversation_id, reply, summary, user_query, scope)

    def ingest_document(
        self,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        scope: Optional[MemoryScope] = None,
        source_id: str = "",
    ) -> Dict[str, Any]:
        if not self.enabled:
            return {"enabled": False, "stored": 0}
        if self.async_ingest:
            self._queue.put(("document", (title, content, tags, scope, source_id), {}))
            return {"enabled": True, "queued": True}
        return self._ingest_document(title, content, tags, scope, source_id)

    def _ingest_document(
        self,
        title: str,
        content: str,
        tags: Optional[List[str]],
        scope: Optional[MemoryScope],
        source_id: str,
    ) -> Dict[str, Any]:
        scope = self._normalize_scope(scope)
        layout, index = self._ensure_scope_storage(scope)
        tags = _clean_list(tags)
        item = self._build_item(
            kind="document",
            title=title,
            content=content,
            tags=tags,
            keywords=tags,
            entities=[],
            project="",
            category="general",
            source_id=source_id,
            confidence="medium",
            scope=scope,
        )
        item.path = layout.item_path(item.id)
        self._write_json(item.path, self._item_payload(item))
        index.upsert_item(self._item_payload(item), scope)
        self._update_category(item.category, scope, index=index, layout=layout)
        if self.graph_enabled:
            self._add_edges_for_item(item, scope, index=index)
        return {"enabled": True, "stored": 1, "item_id": item.id}

    def _ingest_summary(
        self,
        conversation_id: str,
        reply: str,
        summary: Optional[Dict[str, Any]],
        user_query: str,
        scope: Optional[MemoryScope],
    ) -> Dict[str, Any]:
        scope = self._normalize_scope(scope)
        layout, index = self._ensure_scope_storage(scope)
        conversation_id = _safe_str(conversation_id) or _uuid("conv")
        resource = MemoryResource(
            id=_uuid("res"),
            kind="conversation",
            source=conversation_id,
            content=_safe_str(reply),
            metadata={"user_query": _safe_str(user_query)},
            scope=scope,
        )
        resource.path = layout.resource_path(resource.id)
        self._write_json(resource.path, self._resource_payload(resource))
        index.upsert_resource(self._resource_payload(resource), scope)

        stored = 0
        items: List[MemoryItem] = []
        if summary:
            items.extend(self._items_from_summary(summary, resource, scope))
        if user_query:
            items.append(
                self._build_item(
                    kind="query",
                    title=f"User Query {conversation_id}",
                    content=_safe_str(user_query),
                    tags=["query"],
                    keywords=[],
                    entities=[],
                    project=self._infer_project(summary),
                    category=self._infer_category(summary),
                    source_id=resource.id,
                    confidence="medium",
                    scope=scope,
                )
            )

        for item in items:
            item.path = layout.item_path(item.id)
            self._write_json(item.path, self._item_payload(item))
            index.upsert_item(self._item_payload(item), scope)
            stored += 1

        category = self._infer_category(summary)
        if category:
            self._update_category(category, scope, index=index, layout=layout)
        if self.graph_enabled:
            for item in items:
                self._add_edges_for_item(item, scope, index=index)
        return {"enabled": True, "stored": stored, "resource_id": resource.id}

    def _infer_project(self, summary: Optional[Dict[str, Any]]) -> str:
        return str(normalize_typed_context(summary).get("project", "")).strip()

    def _infer_category(self, summary: Optional[Dict[str, Any]]) -> str:
        normalized = sanitize_typed_context_for_durable_write(summary)
        project = str(normalized.get("project", "")).strip()
        if project:
            return project
        topics = list(normalized.get("topics", []) or [])
        if topics:
            return str(topics[0]).strip()
        return "general"

    def _items_from_summary(
        self,
        summary: Dict[str, Any],
        resource: MemoryResource,
        scope: MemoryScope,
    ) -> List[MemoryItem]:
        items: List[MemoryItem] = []
        normalized = sanitize_typed_context_for_durable_write(summary)
        project = self._infer_project(normalized)
        category = self._infer_category(normalized)
        keywords = _clean_list(normalized.get("keywords") or [])
        entities = _clean_list(normalized.get("entities") or [])
        confidence = _safe_str(normalized.get("confidence") or "medium")

        def _add(kind: str, title: str, content: str, extra_tags: Optional[List[str]] = None) -> None:
            content = _safe_str(content)
            if not content:
                return
            tags = [kind] + (extra_tags or []) + keywords
            items.append(
                self._build_item(
                    kind=kind,
                    title=title,
                    content=content,
                    tags=tags,
                    keywords=keywords,
                    entities=entities,
                    project=project,
                    category=category,
                    source_id=resource.id,
                    confidence=confidence,
                    scope=scope,
                )
            )

        _add("summary", "摘要", normalized.get("summary"))
        _add("goal", "目标", normalized.get("goal"))
        _add("status", "状态", normalized.get("status"))
        for decision in normalized.get("decisions") or []:
            _add("decision", "决策上下文", decision)
        for constraint in normalized.get("constraints") or []:
            _add("constraint", "约束", constraint)
        for blocker in normalized.get("blockers") or []:
            _add("blocker", "阻塞与风险", blocker)
        for action in normalized.get("next_actions") or []:
            _add("next", "下一步", action)
        for question in normalized.get("questions") or []:
            _add("questions", "待澄清问题", question)
        for evidence in normalized.get("evidence") or []:
            _add("evidence", "证据指针", evidence)
        for replay in normalized.get("replay") or []:
            _add("replay", "复现命令", replay)
        for topic in normalized.get("topics") or []:
            _add("topic", "主题", topic)
        for tp in normalized.get("tech_points") or []:
            _add("tech_point", "技术要点", tp)
        _add("code_pattern", "代码模式", normalized.get("code_pattern"))
        _add("pitfall", "避坑记录", normalized.get("pitfall_record"))
        _add("scene", "适用场景", normalized.get("applicable_scene"))
        return items

    def _item_payload(self, item: MemoryItem) -> Dict[str, Any]:
        return {
            "id": item.id,
            "title": item.title,
            "content": item.content,
            "kind": item.kind,
            "tags": "|".join(item.tags),
            "keywords": "|".join(item.keywords),
            "entities": "|".join(item.entities),
            "project": item.project,
            "category": item.category,
            "source_id": item.source_id,
            "created_at": item.created_at,
            "updated_at": now_iso(),
            "confidence": item.confidence,
            "archived": item.archived,
            "usage_count": item.usage_count,
            "last_used": item.last_used,
            "ttl_days": item.ttl_days,
            "decay_half_life_days": item.decay_half_life_days,
            "archive_after_days": item.archive_after_days,
            "scope_agent": item.scope.agent_id,
            "scope_user": item.scope.user_id,
            "scope_app": item.scope.app_id,
            "scope_run": item.scope.run_id,
            "scope_workspace": item.scope.workspace,
            "path": item.path,
        }

    def _resource_payload(self, resource: MemoryResource) -> Dict[str, Any]:
        return {
            "id": resource.id,
            "kind": resource.kind,
            "source": resource.source,
            "content": resource.content,
            "metadata": json.dumps(resource.metadata, ensure_ascii=False),
            "created_at": resource.created_at,
            "updated_at": now_iso(),
            "scope_agent": resource.scope.agent_id,
            "scope_user": resource.scope.user_id,
            "scope_app": resource.scope.app_id,
            "scope_run": resource.scope.run_id,
            "scope_workspace": resource.scope.workspace,
            "path": resource.path,
        }

    def _category_payload(self, category: MemoryCategory) -> Dict[str, Any]:
        return {
            "id": category.id,
            "name": category.name,
            "summary": category.summary,
            "tags": "|".join(category.tags),
            "created_at": category.created_at,
            "updated_at": now_iso(),
            "scope_agent": category.scope.agent_id,
            "scope_user": category.scope.user_id,
            "scope_app": category.scope.app_id,
            "scope_run": category.scope.run_id,
            "scope_workspace": category.scope.workspace,
            "path": category.path,
        }

    def _category_record_id(self, category_name: str, scope: MemoryScope) -> str:
        normalized_scope = self._normalize_scope(scope)
        slug = "".join(
            ch if (ch.isalnum() or ch in {"_", "-"}) else "_"
            for ch in (_safe_str(category_name).lower() or "general")
        ).strip("_")
        while "__" in slug:
            slug = slug.replace("__", "_")
        slug = slug[:48] or "general"
        digest = hashlib.sha1(normalized_scope.scope_key().encode("utf-8")).hexdigest()[:12]
        return f"cat_{slug}_{digest}"

    def _update_category(
        self,
        category_name: str,
        scope: MemoryScope,
        index: Optional[MemoryIndex] = None,
        layout: Optional[MemoryLayout] = None,
    ) -> None:
        category_name = _safe_str(category_name) or "general"
        scope = self._normalize_scope(scope)
        if index is None or layout is None:
            _layout, _index = self._ensure_scope_storage(scope)
            layout = layout or _layout
            index = index or _index
        items = index.list_items_by_category(category_name, self.category_max_items, scope)
        summary_lines = [
            f"# {category_name}",
            "",
            f"Updated: {now_iso()}",
            "",
            "## Highlights",
        ]
        for item in items[: min(5, len(items))]:
            snippet = str(item.get("content", ""))[:120]
            summary_lines.append(f"- {item.get('title', 'item')}: {snippet}")
        summary_lines.append("")
        summary_lines.append("## Recent Items")
        for item in items:
            tags = str(item.get("tags", ""))
            summary_lines.append(
                f"- [{item.get('kind', 'note')}] {item.get('title', 'item')} ({tags})"
            )
        summary_text = "\n".join(summary_lines)

        category = MemoryCategory(
            id=self._category_record_id(category_name, scope),
            name=category_name,
            summary=summary_text,
            tags=[],
            scope=scope,
        )
        category.path = layout.category_path(category_name)
        with open(category.path, "w", encoding="utf-8") as fh:
            fh.write(summary_text)
        index.upsert_category(self._category_payload(category), scope)

    def _add_edges_for_item(
        self,
        item: MemoryItem,
        scope: MemoryScope,
        index: Optional[MemoryIndex] = None,
    ) -> None:
        scope = self._normalize_scope(scope)
        if index is None:
            _, index = self._ensure_scope_storage(scope)
        keywords = item.keywords or []
        entities = item.entities or []
        if not keywords and not entities:
            return
        for token in keywords:
            edge = MemoryEdge(
                id=_uuid("edge"),
                src_id=item.id,
                dst_id=f"kw:{token}",
                relation="keyword",
                weight=0.6,
                scope=scope,
            )
            index.add_edge(
                {
                    "id": edge.id,
                    "src_id": edge.src_id,
                    "dst_id": edge.dst_id,
                    "relation": edge.relation,
                    "weight": edge.weight,
                    "created_at": edge.created_at,
                    "metadata": json.dumps(edge.metadata, ensure_ascii=False),
                    "scope_agent": scope.agent_id,
                    "scope_user": scope.user_id,
                    "scope_app": scope.app_id,
                    "scope_run": scope.run_id,
                    "scope_workspace": scope.workspace,
                },
                scope,
            )
        for token in entities:
            edge = MemoryEdge(
                id=_uuid("edge"),
                src_id=item.id,
                dst_id=f"ent:{token}",
                relation="entity",
                weight=0.8,
                scope=scope,
            )
            index.add_edge(
                {
                    "id": edge.id,
                    "src_id": edge.src_id,
                    "dst_id": edge.dst_id,
                    "relation": edge.relation,
                    "weight": edge.weight,
                    "created_at": edge.created_at,
                    "metadata": json.dumps(edge.metadata, ensure_ascii=False),
                    "scope_agent": scope.agent_id,
                    "scope_user": scope.user_id,
                    "scope_app": scope.app_id,
                    "scope_run": scope.run_id,
                    "scope_workspace": scope.workspace,
                },
                scope,
            )

    def recall(self, query: str, limit: int = 5, scope: Optional[MemoryScope] = None) -> List[MemoryHit]:
        if not self.enabled:
            return []
        scope = self._normalize_scope(scope)
        _, index = self._ensure_scope_storage(scope)
        items = index.search_items(query, limit * 2, scope)
        hits: List[MemoryHit] = []
        now = datetime.now(timezone.utc)
        for row in items:
            lifecycle = self._item_lifecycle_state(row, now)
            if lifecycle["archived"] or lifecycle["ttl_expired"]:
                continue
            score = row.get("score")
            relevance = 0.45
            if score is not None:
                try:
                    relevance = 1.0 / (1.0 + float(score))
                except Exception:
                    relevance = 0.45
            relevance *= float(lifecycle["decay_multiplier"])
            usage = _safe_int(row.get("usage_count"), 0)
            if usage > 0 and self.usage_boost > 0:
                relevance *= 1.0 + min(0.35, log1p(usage) * self.usage_boost)
            hits.append(
                MemoryHit(
                    id=str(row.get("id")),
                    title=str(row.get("title", "item")),
                    content=str(row.get("content", "")),
                    source=str(row.get("source_id", "")),
                    relevance=float(relevance),
                    origin="memory_v5",
                    metadata={
                        "kind": row.get("kind", "note"),
                        "category": row.get("category", ""),
                        "updated_at": row.get("updated_at", ""),
                        "usage_count": row.get("usage_count", 0),
                    },
                )
            )

        categories = index.search_categories(query, limit, scope)
        for row in categories:
            hits.append(
                MemoryHit(
                    id=str(row.get("id")),
                    title=str(row.get("name", "category")),
                    content=str(row.get("summary", ""))[:400],
                    source=str(row.get("name", "category")),
                    relevance=0.35,
                    origin="category",
                    metadata={"category": row.get("name", "")},
                )
            )

        # Graph expansion
        if self.graph_enabled and hits:
            seed_ids = [h.id for h in hits if h.id.startswith("item_")]
            edges = index.related_edges(seed_ids, scope, limit=30)
            related_ids: List[str] = []
            for edge in edges:
                src = str(edge.get("src_id"))
                dst = str(edge.get("dst_id"))
                if src in seed_ids and dst.startswith("item_"):
                    related_ids.append(dst)
                if dst in seed_ids and src.startswith("item_"):
                    related_ids.append(src)
            if related_ids:
                related_items = index.get_items_by_ids(related_ids, scope)
                for row in related_items:
                    hits.append(
                        MemoryHit(
                            id=str(row.get("id")),
                            title=str(row.get("title", "item")),
                            content=str(row.get("content", "")),
                            source=str(row.get("source_id", "")),
                            relevance=0.25,
                            origin="graph",
                            metadata={"kind": row.get("kind", "note"), "category": row.get("category", "")},
                        )
                    )

        # Deduplicate
        dedup: Dict[str, MemoryHit] = {}
        for hit in hits:
            key = hit.id or (hit.title + hit.content)
            existing = dedup.get(key)
            if existing is None or hit.relevance > existing.relevance:
                dedup[key] = hit
        final = sorted(dedup.values(), key=lambda h: h.relevance, reverse=True)
        final = final[: max(1, int(limit))]
        item_ids = [h.id for h in final if h.id.startswith("item_")]
        if item_ids:
            try:
                index.bump_usage(item_ids)
            except Exception:
                pass
        return final

    def list_items(self, scope: Optional[MemoryScope] = None, include_archived: bool = False) -> List[Dict[str, Any]]:
        scope = self._normalize_scope(scope)
        _, index = self._ensure_scope_storage(scope)
        return index.list_all_items(scope, include_archived=include_archived)

    def archive_item(self, item_id: str, scope: Optional[MemoryScope] = None) -> bool:
        scope = self._normalize_scope(scope)
        if not item_id:
            return False
        layout, index = self._ensure_scope_storage(scope)
        item_path = layout.item_path(item_id)
        archive_path = layout.item_archive_path(item_id)
        try:
            if os.path.exists(item_path):
                os.replace(item_path, archive_path)
            index.set_archived(item_id, archived=1)
            return True
        except Exception:
            return False

    def audit_lifecycle(
        self,
        scope: Optional[MemoryScope] = None,
        now_ts: Optional[Any] = None,
        sample_limit: int = 10,
    ) -> Dict[str, Any]:
        scope = self._normalize_scope(scope)
        if not self.enabled:
            return {
                "enabled": False,
                "generated_at": self._resolve_now(now_ts).isoformat(),
                "scope": self._lifecycle_scope_payload(scope),
                "defaults": {
                    "ttl_days_default": self.ttl_days_default,
                    "decay_half_life_days_default": self.decay_half_life_days_default,
                    "archive_after_days": self.archive_after_days,
                },
                "counts": {
                    "total": 0,
                    "active": 0,
                    "archived": 0,
                    "ttl_expired": 0,
                    "archive_due": 0,
                    "decaying": 0,
                    "archive_backfill_candidates": 0,
                },
                "samples": {},
            }

        sample_limit = max(1, _safe_int(sample_limit, 10))
        now = self._resolve_now(now_ts)
        rows = self._load_lifecycle_rows(scope, now)
        counts = {
            "total": 0,
            "active": 0,
            "archived": 0,
            "ttl_expired": 0,
            "archive_due": 0,
            "decaying": 0,
            "archive_backfill_candidates": 0,
        }
        sample_buckets: Dict[str, List[Dict[str, Any]]] = {
            "archived": [],
            "ttl_expired": [],
            "archive_due": [],
            "decaying": [],
            "archive_backfill_candidates": [],
        }

        for row, lifecycle in rows:
            counts["total"] += 1
            sample = self._lifecycle_sample_payload(row, lifecycle)
            if lifecycle["archived"]:
                counts["archived"] += 1
                sample_buckets["archived"].append(sample)
            if lifecycle["ttl_expired"]:
                counts["ttl_expired"] += 1
                sample_buckets["ttl_expired"].append(sample)
            if lifecycle["archive_due"]:
                counts["archive_due"] += 1
                sample_buckets["archive_due"].append(sample)
            if (not lifecycle["archived"]) and float(lifecycle["decay_multiplier"]) < 0.999999:
                counts["decaying"] += 1
                sample_buckets["decaying"].append(sample)
            if not lifecycle["archived"] and not lifecycle["ttl_expired"] and not lifecycle["archive_due"]:
                counts["active"] += 1
            backfill_candidate = self._archive_backfill_candidate_payload(row, lifecycle)
            if backfill_candidate:
                counts["archive_backfill_candidates"] += 1
                sample_buckets["archive_backfill_candidates"].append(backfill_candidate)

        samples = {
            name: sorted(bucket, key=lambda item: float(item["age_days"]), reverse=True)[:sample_limit]
            for name, bucket in sample_buckets.items()
            if bucket
        }
        return {
            "enabled": True,
            "generated_at": now.isoformat(),
            "scope": self._lifecycle_scope_payload(scope),
            "defaults": {
                "ttl_days_default": self.ttl_days_default,
                "decay_half_life_days_default": self.decay_half_life_days_default,
                "archive_after_days": self.archive_after_days,
            },
            "counts": counts,
            "samples": samples,
        }

    def backfill_archive_defaults(
        self,
        scope: Optional[MemoryScope] = None,
        now_ts: Optional[Any] = None,
        max_items: int = 100,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        scope = self._normalize_scope(scope)
        now = self._resolve_now(now_ts)
        if not self.enabled:
            return {
                "enabled": False,
                "generated_at": now.isoformat(),
                "scope": self._lifecycle_scope_payload(scope),
                "dry_run": bool(dry_run),
                "matched": 0,
                "selected": 0,
                "updated": 0,
                "failed": 0,
                "candidate_ids": [],
                "updated_ids": [],
                "failed_ids": [],
                "candidates": [],
            }

        max_items = max(1, _safe_int(max_items, 100))
        candidates: List[Dict[str, Any]] = []
        for row, lifecycle in self._load_lifecycle_rows(scope, now):
            candidate = self._archive_backfill_candidate_payload(row, lifecycle)
            if candidate:
                candidates.append(candidate)
        candidates.sort(key=lambda item: float(item.get("age_days", 0.0)), reverse=True)
        selected = candidates[:max_items]
        candidate_ids = [str(item.get("id", "")) for item in selected if str(item.get("id", ""))]
        updated_ids: List[str] = []
        failed_ids: List[str] = []
        _, index = self._ensure_scope_storage(scope)
        if not dry_run:
            for candidate in selected:
                item_id = str(candidate.get("id", ""))
                archive_after_days = _safe_int(candidate.get("resolved_archive_after_days"), 0)
                if item_id and archive_after_days > 0 and index.set_item_archive_after_days(
                    item_id,
                    archive_after_days,
                    scope=scope,
                ):
                    updated_ids.append(item_id)
                elif item_id:
                    failed_ids.append(item_id)
        return {
            "enabled": True,
            "generated_at": now.isoformat(),
            "scope": self._lifecycle_scope_payload(scope),
            "dry_run": bool(dry_run),
            "matched": len(candidates),
            "selected": len(selected),
            "updated": len(updated_ids),
            "failed": len(failed_ids),
            "candidate_ids": candidate_ids,
            "updated_ids": updated_ids,
            "failed_ids": failed_ids,
            "candidates": selected,
        }

    def archive_due_items(
        self,
        scope: Optional[MemoryScope] = None,
        now_ts: Optional[Any] = None,
        max_items: int = 100,
        dry_run: bool = True,
        include_ttl_expired: bool = False,
    ) -> Dict[str, Any]:
        scope = self._normalize_scope(scope)
        now = self._resolve_now(now_ts)
        if not self.enabled:
            return {
                "enabled": False,
                "generated_at": now.isoformat(),
                "scope": self._lifecycle_scope_payload(scope),
                "dry_run": bool(dry_run),
                "include_ttl_expired": bool(include_ttl_expired),
                "matched": 0,
                "selected": 0,
                "archived": 0,
                "failed": 0,
                "candidate_ids": [],
                "archived_ids": [],
                "failed_ids": [],
            }

        max_items = max(1, _safe_int(max_items, 100))
        due_rows = [
            (row, lifecycle)
            for row, lifecycle in self._load_lifecycle_rows(scope, now)
            if lifecycle["archive_due"] or (include_ttl_expired and lifecycle["ttl_expired"] and not lifecycle["archived"])
        ]
        due_rows.sort(key=lambda item: float(item[1]["age_days"]), reverse=True)
        selected = due_rows[:max_items]
        candidate_ids = [str(row.get("id", "")) for row, _ in selected if str(row.get("id", ""))]
        archived_ids: List[str] = []
        failed_ids: List[str] = []
        if not dry_run:
            for item_id in candidate_ids:
                if self.archive_item(item_id, scope=scope):
                    archived_ids.append(item_id)
                else:
                    failed_ids.append(item_id)
        return {
            "enabled": True,
            "generated_at": now.isoformat(),
            "scope": self._lifecycle_scope_payload(scope),
            "dry_run": bool(dry_run),
            "include_ttl_expired": bool(include_ttl_expired),
            "matched": len(due_rows),
            "selected": len(candidate_ids),
            "archived": len(archived_ids),
            "failed": len(failed_ids),
            "candidate_ids": candidate_ids,
            "archived_ids": archived_ids,
            "failed_ids": failed_ids,
        }
