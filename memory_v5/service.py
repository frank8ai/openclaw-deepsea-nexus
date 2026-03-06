from __future__ import annotations

import json
import os
import threading
import queue
import uuid
from datetime import datetime, timezone
from math import log1p
from typing import Any, Dict, List, Optional

from .models import MemoryScope, MemoryResource, MemoryItem, MemoryCategory, MemoryEdge, MemoryHit, now_iso
from .layout import MemoryLayout
from .index import MemoryIndex


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
    mem_cfg = config.get("memory_v5", {}) if isinstance(config, dict) else {}
    root = mem_cfg.get("root") or "memory/95_MemoryV5"
    paths = config.get("paths", {}) if isinstance(config.get("paths", {}), dict) else {}
    base = paths.get("base") or config.get("base_path") or config.get("workspace_root") or os.getcwd()
    root = os.path.expanduser(str(root))
    if os.path.isabs(root):
        return root
    return os.path.join(os.path.expanduser(str(base)), root)


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
        self.root = _resolve_root(self.config)
        self.scope = _default_scope(self.config)
        self.layout = MemoryLayout(self.root, self.scope)
        self.layout.ensure_dirs()
        self.index = MemoryIndex(self.layout.index_path(), fts_enabled=self.fts_enabled)
        self._queue: "queue.Queue[tuple]" = queue.Queue()
        self._worker: Optional[threading.Thread] = None
        if self.enabled and self.async_ingest:
            self._start_worker()

    def _start_worker(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

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
        scope = scope or self.scope
        tags = _clean_list(tags)
        item = MemoryItem(
            id=_uuid("item"),
            title=_safe_str(title) or "Untitled",
            content=_safe_str(content),
            kind="document",
            tags=tags,
            keywords=tags,
            entities=[],
            project="",
            category="general",
            source_id=source_id,
            confidence="medium",
            ttl_days=self.ttl_days_default,
            decay_half_life_days=self.decay_half_life_days_default,
            scope=scope,
        )
        item.path = self.layout.item_path(item.id)
        self._write_json(item.path, self._item_payload(item))
        self.index.upsert_item(self._item_payload(item), scope)
        self._update_category(item.category, scope)
        if self.graph_enabled:
            self._add_edges_for_item(item, scope)
        return {"enabled": True, "stored": 1, "item_id": item.id}

    def _ingest_summary(
        self,
        conversation_id: str,
        reply: str,
        summary: Optional[Dict[str, Any]],
        user_query: str,
        scope: Optional[MemoryScope],
    ) -> Dict[str, Any]:
        scope = scope or self.scope
        conversation_id = _safe_str(conversation_id) or _uuid("conv")
        resource = MemoryResource(
            id=_uuid("res"),
            kind="conversation",
            source=conversation_id,
            content=_safe_str(reply),
            metadata={"user_query": _safe_str(user_query)},
            scope=scope,
        )
        resource.path = self.layout.resource_path(resource.id)
        self._write_json(resource.path, self._resource_payload(resource))
        self.index.upsert_resource(self._resource_payload(resource), scope)

        stored = 0
        items: List[MemoryItem] = []
        if summary:
            items.extend(self._items_from_summary(summary, resource, scope))
        if user_query:
            items.append(
                MemoryItem(
                    id=_uuid("item"),
                    title=f"User Query {conversation_id}",
                    content=_safe_str(user_query),
                    kind="query",
                    tags=["query"],
                    keywords=[],
                    entities=[],
                    project=self._infer_project(summary),
                    category=self._infer_category(summary),
                    source_id=resource.id,
                    confidence="medium",
                    ttl_days=self.ttl_days_default,
                    decay_half_life_days=self.decay_half_life_days_default,
                    scope=scope,
                )
            )

        for item in items:
            item.path = self.layout.item_path(item.id)
            self._write_json(item.path, self._item_payload(item))
            self.index.upsert_item(self._item_payload(item), scope)
            stored += 1

        category = self._infer_category(summary)
        if category:
            self._update_category(category, scope)
        if self.graph_enabled:
            for item in items:
                self._add_edges_for_item(item, scope)
        return {"enabled": True, "stored": stored, "resource_id": resource.id}

    def _infer_project(self, summary: Optional[Dict[str, Any]]) -> str:
        if not summary:
            return ""
        for key in ["项目关联", "project", "project_name", "project关联"]:
            val = summary.get(key) if isinstance(summary, dict) else ""
            if val:
                return str(val).strip()
        return ""

    def _infer_category(self, summary: Optional[Dict[str, Any]]) -> str:
        project = self._infer_project(summary)
        if project:
            return project
        if summary and isinstance(summary, dict):
            val = summary.get("主题") or summary.get("topic")
            if val:
                return str(val).strip()
        return "general"

    def _items_from_summary(
        self,
        summary: Dict[str, Any],
        resource: MemoryResource,
        scope: MemoryScope,
    ) -> List[MemoryItem]:
        items: List[MemoryItem] = []
        project = self._infer_project(summary)
        category = self._infer_category(summary)
        keywords = _clean_list(summary.get("搜索关键词") or summary.get("keywords") or [])
        entities = _clean_list(summary.get("实体") or summary.get("entities") or [])
        confidence = _safe_str(summary.get("置信度") or summary.get("confidence") or "medium")

        def _add(kind: str, title: str, content: str, extra_tags: Optional[List[str]] = None) -> None:
            content = _safe_str(content)
            if not content:
                return
            tags = [kind] + (extra_tags or []) + keywords
            items.append(
                MemoryItem(
                    id=_uuid("item"),
                    title=title,
                    content=content,
                    kind=kind,
                    tags=_clean_list(tags),
                    keywords=keywords,
                    entities=entities,
                    project=project,
                    category=category,
                    source_id=resource.id,
                    confidence=confidence,
                    ttl_days=self.ttl_days_default,
                    decay_half_life_days=self.decay_half_life_days_default,
                    scope=scope,
                )
            )

        _add("core_output", "核心产出", summary.get("本次核心产出") or summary.get("core_output"))
        tech_points = summary.get("技术要点") or summary.get("tech_points") or []
        if isinstance(tech_points, list):
            for tp in tech_points:
                _add("tech_point", "技术要点", tp)
        _add("code_pattern", "代码模式", summary.get("代码模式") or summary.get("code_pattern"))
        _add("decision", "决策上下文", summary.get("决策上下文") or summary.get("decision_context"))
        _add("pitfall", "避坑记录", summary.get("避坑记录") or summary.get("pitfall_record"))
        _add("scene", "适用场景", summary.get("适用场景") or summary.get("applicable_scene"))
        _add("next", "下一步", summary.get("下一步") or summary.get("next_actions"))
        _add("questions", "待澄清问题", summary.get("问题") or summary.get("questions"))
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

    def _update_category(self, category_name: str, scope: MemoryScope) -> None:
        category_name = _safe_str(category_name) or "general"
        items = self.index.list_items_by_category(category_name, self.category_max_items, scope)
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
            id=f"cat_{category_name}",
            name=category_name,
            summary=summary_text,
            tags=[],
            scope=scope,
        )
        category.path = self.layout.category_path(category_name)
        with open(category.path, "w", encoding="utf-8") as fh:
            fh.write(summary_text)
        self.index.upsert_category(self._category_payload(category), scope)

    def _add_edges_for_item(self, item: MemoryItem, scope: MemoryScope) -> None:
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
            self.index.add_edge(
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
            self.index.add_edge(
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
        scope = scope or self.scope
        items = self.index.search_items(query, limit * 2, scope)
        hits: List[MemoryHit] = []
        now = datetime.now(timezone.utc)
        for row in items:
            ttl_days = int(row.get("ttl_days") or 0)
            updated_at = row.get("updated_at") or row.get("created_at")
            age_days = 0.0
            if updated_at:
                try:
                    ts = datetime.fromisoformat(str(updated_at))
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    age_days = max(0.0, (now - ts).total_seconds() / 86400.0)
                except Exception:
                    age_days = 0.0
            if ttl_days > 0 and age_days > ttl_days:
                continue
            score = row.get("score")
            relevance = 0.45
            if score is not None:
                try:
                    relevance = 1.0 / (1.0 + float(score))
                except Exception:
                    relevance = 0.45
            half_life = int(row.get("decay_half_life_days") or self.decay_half_life_days_default or 0)
            if half_life > 0 and age_days > 0:
                relevance *= 0.5 ** (age_days / float(half_life))
            usage = int(row.get("usage_count") or 0)
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

        categories = self.index.search_categories(query, limit, scope)
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
            edges = self.index.related_edges(seed_ids, scope, limit=30)
            related_ids: List[str] = []
            for edge in edges:
                src = str(edge.get("src_id"))
                dst = str(edge.get("dst_id"))
                if src in seed_ids and dst.startswith("item_"):
                    related_ids.append(dst)
                if dst in seed_ids and src.startswith("item_"):
                    related_ids.append(src)
            if related_ids:
                related_items = self.index.get_items_by_ids(related_ids, scope)
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
                self.index.bump_usage(item_ids)
            except Exception:
                pass
        return final

    def archive_item(self, item_id: str, scope: Optional[MemoryScope] = None) -> bool:
        scope = scope or self.scope
        if not item_id:
            return False
        item_path = self.layout.item_path(item_id)
        archive_path = self.layout.item_archive_path(item_id)
        try:
            if os.path.exists(item_path):
                os.replace(item_path, archive_path)
            self.index.set_archived(item_id, archived=1)
            return True
        except Exception:
            return False
