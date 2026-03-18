from __future__ import annotations

import os
import sqlite3
import threading
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .models import MemoryScope


class MemoryIndex:
    def __init__(self, db_path: str, fts_enabled: bool = True) -> None:
        self.db_path = os.path.expanduser(db_path)
        self._lock = threading.Lock()
        self._conn: Optional[sqlite3.Connection] = None
        self.fts_enabled = bool(fts_enabled)
        self._ensure_connection()
        self._ensure_schema()

    def _ensure_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _ensure_schema(self) -> None:
        conn = self._ensure_connection()
        with self._lock:
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS resources (
                        id TEXT PRIMARY KEY,
                        kind TEXT,
                        source TEXT,
                        content TEXT,
                        metadata TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        scope_agent TEXT,
                        scope_user TEXT,
                        scope_app TEXT,
                        scope_run TEXT,
                        scope_workspace TEXT
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS items (
                        id TEXT PRIMARY KEY,
                        title TEXT,
                        content TEXT,
                        kind TEXT,
                        tags TEXT,
                        keywords TEXT,
                        entities TEXT,
                        project TEXT,
                        category TEXT,
                        source_id TEXT,
                        metadata TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        confidence TEXT,
                        scope_agent TEXT,
                        scope_user TEXT,
                        scope_app TEXT,
                        scope_run TEXT,
                        scope_workspace TEXT
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS categories (
                        id TEXT PRIMARY KEY,
                        name TEXT,
                        summary TEXT,
                        tags TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        scope_agent TEXT,
                        scope_user TEXT,
                        scope_app TEXT,
                        scope_run TEXT,
                        scope_workspace TEXT
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS edges (
                        id TEXT PRIMARY KEY,
                        src_id TEXT,
                        dst_id TEXT,
                        relation TEXT,
                        weight REAL,
                        created_at TEXT,
                        metadata TEXT,
                        scope_agent TEXT,
                        scope_user TEXT,
                        scope_app TEXT,
                        scope_run TEXT,
                        scope_workspace TEXT
                    )
                    """
                )
                conn.commit()
                if self.fts_enabled:
                    try:
                        cur.execute(
                            """
                            CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(
                                title, content, tags, keywords, entities, project, category,
                                content='items', content_rowid='rowid'
                            )
                            """
                        )
                        cur.execute(
                            """
                            CREATE VIRTUAL TABLE IF NOT EXISTS categories_fts USING fts5(
                                name, summary, tags,
                                content='categories', content_rowid='rowid'
                            )
                            """
                        )
                        conn.commit()
                    except sqlite3.OperationalError:
                        self.fts_enabled = False
                self._ensure_columns()
            except sqlite3.DatabaseError:
                # Corrupt DB: archive and recreate
                try:
                    conn.close()
                except Exception:
                    pass
                self._conn = None
                corrupt_path = self.db_path + ".corrupt"
                try:
                    if os.path.exists(self.db_path):
                        os.replace(self.db_path, corrupt_path)
                except Exception:
                    pass
                self._ensure_connection()
                self.fts_enabled = False
                self._ensure_schema()

    def _ensure_columns(self) -> None:
        conn = self._ensure_connection()
        existing = {row[1] for row in conn.execute("PRAGMA table_info(items)").fetchall()}
        wanted = {
            "metadata": "TEXT",
            "archived": "INTEGER DEFAULT 0",
            "usage_count": "INTEGER DEFAULT 0",
            "last_used": "TEXT",
            "ttl_days": "INTEGER DEFAULT 0",
            "decay_half_life_days": "INTEGER DEFAULT 0",
            "archive_after_days": "INTEGER DEFAULT 0",
        }
        for col, ddl in wanted.items():
            if col in existing:
                continue
            try:
                conn.execute(f"ALTER TABLE items ADD COLUMN {col} {ddl}")
            except sqlite3.DatabaseError:
                continue
        conn.commit()

    def _scope_where(self, scope: MemoryScope) -> Tuple[str, Tuple[str, ...]]:
        scope = scope.normalized()
        clause = (
            "scope_agent=? AND scope_user=? AND scope_app=? AND scope_run=? AND scope_workspace=?"
        )
        params = (scope.agent_id, scope.user_id, scope.app_id, scope.run_id, scope.workspace)
        return clause, params

    def _serialize_list(self, items: List[str]) -> str:
        return "|".join([str(x).strip() for x in items if str(x).strip()])

    def _parse_list(self, value: Optional[str]) -> List[str]:
        if not value:
            return []
        return [x for x in str(value).split("|") if x]

    def upsert_resource(self, record: Dict[str, str], scope: MemoryScope) -> None:
        conn = self._ensure_connection()
        clause, params = self._scope_where(scope)
        payload = dict(record)
        payload.setdefault("scope_agent", params[0])
        payload.setdefault("scope_user", params[1])
        payload.setdefault("scope_app", params[2])
        payload.setdefault("scope_run", params[3])
        payload.setdefault("scope_workspace", params[4])
        with self._lock:
            conn.execute(
                """
                INSERT INTO resources (
                    id, kind, source, content, metadata, created_at, updated_at,
                    scope_agent, scope_user, scope_app, scope_run, scope_workspace
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    kind=excluded.kind,
                    source=excluded.source,
                    content=excluded.content,
                    metadata=excluded.metadata,
                    updated_at=excluded.updated_at
                """,
                (
                    payload.get("id"),
                    payload.get("kind"),
                    payload.get("source"),
                    payload.get("content"),
                    payload.get("metadata"),
                    payload.get("created_at"),
                    payload.get("updated_at"),
                    payload.get("scope_agent"),
                    payload.get("scope_user"),
                    payload.get("scope_app"),
                    payload.get("scope_run"),
                    payload.get("scope_workspace"),
                ),
            )
            conn.commit()

    def _refresh_item_fts(self, rowid: int, payload: Dict[str, str]) -> None:
        if not self.fts_enabled:
            return
        conn = self._ensure_connection()
        try:
            conn.execute("DELETE FROM items_fts WHERE rowid=?", (rowid,))
            conn.execute(
                """
                INSERT INTO items_fts (rowid, title, content, tags, keywords, entities, project, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rowid,
                    payload.get("title", ""),
                    payload.get("content", ""),
                    payload.get("tags", ""),
                    payload.get("keywords", ""),
                    payload.get("entities", ""),
                    payload.get("project", ""),
                    payload.get("category", ""),
                ),
            )
            conn.commit()
        except sqlite3.DatabaseError:
            # FTS corruption or mismatch: disable FTS and continue in lexical mode.
            self.fts_enabled = False

    def upsert_item(self, record: Dict[str, str], scope: MemoryScope) -> None:
        conn = self._ensure_connection()
        payload = dict(record)
        clause, params = self._scope_where(scope)
        payload.setdefault("scope_agent", params[0])
        payload.setdefault("scope_user", params[1])
        payload.setdefault("scope_app", params[2])
        payload.setdefault("scope_run", params[3])
        payload.setdefault("scope_workspace", params[4])

        with self._lock:
            conn.execute(
                """
                INSERT INTO items (
                    id, title, content, kind, tags, keywords, entities, project, category,
                    source_id, metadata, created_at, updated_at, confidence, archived, usage_count, last_used, ttl_days, decay_half_life_days, archive_after_days,
                    scope_agent, scope_user, scope_app, scope_run, scope_workspace
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    content=excluded.content,
                    kind=excluded.kind,
                    tags=excluded.tags,
                    keywords=excluded.keywords,
                    entities=excluded.entities,
                    project=excluded.project,
                    category=excluded.category,
                    source_id=excluded.source_id,
                    metadata=excluded.metadata,
                    updated_at=excluded.updated_at,
                    confidence=excluded.confidence,
                    archived=excluded.archived,
                    usage_count=excluded.usage_count,
                    last_used=excluded.last_used,
                    ttl_days=excluded.ttl_days,
                    decay_half_life_days=excluded.decay_half_life_days,
                    archive_after_days=excluded.archive_after_days
                """,
                (
                    payload.get("id"),
                    payload.get("title"),
                    payload.get("content"),
                    payload.get("kind"),
                    payload.get("tags"),
                    payload.get("keywords"),
                    payload.get("entities"),
                    payload.get("project"),
                    payload.get("category"),
                    payload.get("source_id"),
                    payload.get("metadata"),
                    payload.get("created_at"),
                    payload.get("updated_at"),
                    payload.get("confidence"),
                    payload.get("archived", 0),
                    payload.get("usage_count", 0),
                    payload.get("last_used", ""),
                    payload.get("ttl_days", 0),
                    payload.get("decay_half_life_days", 0),
                    payload.get("archive_after_days", 0),
                    payload.get("scope_agent"),
                    payload.get("scope_user"),
                    payload.get("scope_app"),
                    payload.get("scope_run"),
                    payload.get("scope_workspace"),
                ),
            )
            conn.commit()
            rowid = conn.execute("SELECT rowid FROM items WHERE id=?", (payload.get("id"),)).fetchone()
            if rowid:
                self._refresh_item_fts(int(rowid[0]), payload)

    def _refresh_category_fts(self, rowid: int, payload: Dict[str, str]) -> None:
        if not self.fts_enabled:
            return
        conn = self._ensure_connection()
        try:
            conn.execute("DELETE FROM categories_fts WHERE rowid=?", (rowid,))
            conn.execute(
                """
                INSERT INTO categories_fts (rowid, name, summary, tags)
                VALUES (?, ?, ?, ?)
                """,
                (rowid, payload.get("name", ""), payload.get("summary", ""), payload.get("tags", "")),
            )
            conn.commit()
        except sqlite3.DatabaseError:
            self.fts_enabled = False

    def upsert_category(self, record: Dict[str, str], scope: MemoryScope) -> None:
        conn = self._ensure_connection()
        payload = dict(record)
        clause, params = self._scope_where(scope)
        payload.setdefault("scope_agent", params[0])
        payload.setdefault("scope_user", params[1])
        payload.setdefault("scope_app", params[2])
        payload.setdefault("scope_run", params[3])
        payload.setdefault("scope_workspace", params[4])
        with self._lock:
            conn.execute(
                """
                INSERT INTO categories (
                    id, name, summary, tags, created_at, updated_at,
                    scope_agent, scope_user, scope_app, scope_run, scope_workspace
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    summary=excluded.summary,
                    tags=excluded.tags,
                    updated_at=excluded.updated_at
                """,
                (
                    payload.get("id"),
                    payload.get("name"),
                    payload.get("summary"),
                    payload.get("tags"),
                    payload.get("created_at"),
                    payload.get("updated_at"),
                    payload.get("scope_agent"),
                    payload.get("scope_user"),
                    payload.get("scope_app"),
                    payload.get("scope_run"),
                    payload.get("scope_workspace"),
                ),
            )
            conn.commit()
            rowid = conn.execute("SELECT rowid FROM categories WHERE id=?", (payload.get("id"),)).fetchone()
            if rowid:
                self._refresh_category_fts(int(rowid[0]), payload)

    def add_edge(self, record: Dict[str, str], scope: MemoryScope) -> None:
        conn = self._ensure_connection()
        payload = dict(record)
        clause, params = self._scope_where(scope)
        payload.setdefault("scope_agent", params[0])
        payload.setdefault("scope_user", params[1])
        payload.setdefault("scope_app", params[2])
        payload.setdefault("scope_run", params[3])
        payload.setdefault("scope_workspace", params[4])
        with self._lock:
            conn.execute(
                """
                INSERT INTO edges (
                    id, src_id, dst_id, relation, weight, created_at, metadata,
                    scope_agent, scope_user, scope_app, scope_run, scope_workspace
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    src_id=excluded.src_id,
                    dst_id=excluded.dst_id,
                    relation=excluded.relation,
                    weight=excluded.weight,
                    metadata=excluded.metadata
                """,
                (
                    payload.get("id"),
                    payload.get("src_id"),
                    payload.get("dst_id"),
                    payload.get("relation"),
                    payload.get("weight"),
                    payload.get("created_at"),
                    payload.get("metadata"),
                    payload.get("scope_agent"),
                    payload.get("scope_user"),
                    payload.get("scope_app"),
                    payload.get("scope_run"),
                    payload.get("scope_workspace"),
                ),
            )
            conn.commit()

    def _query_terms(self, query: str) -> List[str]:
        raw_tokens = re.findall(r"[\w\u4e00-\u9fff]+", (query or "").lower())
        out: List[str] = []
        for token in raw_tokens:
            val = token.strip()
            if not val:
                continue
            if val not in out:
                out.append(val)
            # For long CJK phrases, add short fragments to improve recall.
            if re.search(r"[\u4e00-\u9fff]", val) and len(val) > 2:
                for n in (2, 3):
                    if len(val) < n:
                        continue
                    for i in range(0, len(val) - n + 1):
                        frag = val[i : i + n]
                        if frag not in out:
                            out.append(frag)
        return out

    def _fts_query(self, query: str) -> str:
        tokens = self._query_terms(query)
        if not tokens:
            return ""
        # Use OR for natural-language questions to avoid over-strict MATCH semantics.
        return " OR ".join([f"\"{tok}\"" for tok in tokens[:16]])

    def _lexical_match_rows(
        self,
        rows: List[sqlite3.Row],
        query: str,
        fields: List[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        terms = self._query_terms(query)
        if not terms:
            return []
        q = (query or "").strip().lower()
        matched: List[Tuple[int, Dict[str, Any]]] = []
        for row in rows:
            row_dict = dict(row)
            text = " ".join([str(row_dict.get(field, "")) for field in fields]).lower()
            if not text.strip():
                continue
            score = 0
            if q and q in text:
                score += 3
            for term in terms:
                if term and term in text:
                    score += 1
            if score > 0:
                matched.append((score, row_dict))
        matched.sort(
            key=lambda item: (
                item[0],
                str(item[1].get("updated_at", "")),
                str(item[1].get("created_at", "")),
            ),
            reverse=True,
        )
        return [row for _score, row in matched[: max(1, int(limit))]]

    def search_items(self, query: str, limit: int, scope: MemoryScope) -> List[Dict[str, str]]:
        conn = self._ensure_connection()
        clause, params = self._scope_where(scope)
        query = (query or "").strip()
        if not query:
            return []
        with self._lock:
            if self.fts_enabled:
                fts_query = self._fts_query(query)
                if not fts_query:
                    return []
                try:
                    rows = conn.execute(
                        f"""
                        SELECT items.*, bm25(items_fts) AS score
                        FROM items_fts
                        JOIN items ON items_fts.rowid = items.rowid
                        WHERE items_fts MATCH ? AND {clause} AND archived=0
                        ORDER BY score ASC
                        LIMIT ?
                        """,
                        (fts_query, *params, int(limit)),
                    ).fetchall()
                    if rows:
                        return [dict(row) for row in rows]
                except sqlite3.DatabaseError:
                    self.fts_enabled = False

            rows = conn.execute(
                f"""
                SELECT * FROM items
                WHERE {clause} AND archived=0
                """,
                params,
            ).fetchall()
            return self._lexical_match_rows(
                rows,
                query,
                ["title", "content", "tags", "keywords", "entities", "project", "category"],
                limit,
            )

    def search_categories(self, query: str, limit: int, scope: MemoryScope) -> List[Dict[str, str]]:
        conn = self._ensure_connection()
        clause, params = self._scope_where(scope)
        query = (query or "").strip()
        if not query:
            return []
        with self._lock:
            if self.fts_enabled:
                fts_query = self._fts_query(query)
                if not fts_query:
                    return []
                try:
                    rows = conn.execute(
                        f"""
                        SELECT categories.*, bm25(categories_fts) AS score
                        FROM categories_fts
                        JOIN categories ON categories_fts.rowid = categories.rowid
                        WHERE categories_fts MATCH ? AND {clause}
                        ORDER BY score ASC
                        LIMIT ?
                        """,
                        (fts_query, *params, int(limit)),
                    ).fetchall()
                    if rows:
                        return [dict(row) for row in rows]
                except sqlite3.DatabaseError:
                    self.fts_enabled = False

            rows = conn.execute(
                f"""
                SELECT * FROM categories
                WHERE {clause}
                """,
                params,
            ).fetchall()
            return self._lexical_match_rows(rows, query, ["name", "summary", "tags"], limit)

    def get_items_by_ids(self, ids: List[str], scope: MemoryScope) -> List[Dict[str, str]]:
        if not ids:
            return []
        conn = self._ensure_connection()
        clause, params = self._scope_where(scope)
        placeholders = ",".join(["?"] * len(ids))
        with self._lock:
            rows = conn.execute(
                f"""
                SELECT * FROM items
                WHERE id IN ({placeholders}) AND {clause}
                """,
                (*ids, *params),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_recent_items(self, limit: int, scope: MemoryScope) -> List[Dict[str, str]]:
        conn = self._ensure_connection()
        clause, params = self._scope_where(scope)
        with self._lock:
            rows = conn.execute(
                f"""
                SELECT * FROM items
                WHERE {clause} AND archived=0
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (*params, int(limit)),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_items_by_category(self, category: str, limit: int, scope: MemoryScope) -> List[Dict[str, str]]:
        conn = self._ensure_connection()
        clause, params = self._scope_where(scope)
        with self._lock:
            rows = conn.execute(
                f"""
                SELECT * FROM items
                WHERE category=? AND {clause} AND archived=0
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (category, *params, int(limit)),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_all_items(self, scope: MemoryScope, include_archived: bool = False) -> List[Dict[str, str]]:
        conn = self._ensure_connection()
        clause, params = self._scope_where(scope)
        with self._lock:
            if include_archived:
                rows = conn.execute(
                    f"SELECT * FROM items WHERE {clause}",
                    params,
                ).fetchall()
            else:
                rows = conn.execute(
                    f"SELECT * FROM items WHERE {clause} AND archived=0",
                    params,
                ).fetchall()
            return [dict(row) for row in rows]

    def set_archived(self, item_id: str, archived: int = 1) -> None:
        if not item_id:
            return
        conn = self._ensure_connection()
        with self._lock:
            conn.execute(
                "UPDATE items SET archived=? WHERE id=?",
                (int(archived), item_id),
            )
            conn.commit()

    def set_item_archive_after_days(
        self,
        item_id: str,
        archive_after_days: int,
        scope: Optional[MemoryScope] = None,
    ) -> bool:
        if not item_id:
            return False
        conn = self._ensure_connection()
        with self._lock:
            if scope is None:
                cur = conn.execute(
                    "UPDATE items SET archive_after_days=? WHERE id=?",
                    (int(archive_after_days), item_id),
                )
            else:
                clause, params = self._scope_where(scope)
                cur = conn.execute(
                    f"UPDATE items SET archive_after_days=? WHERE id=? AND {clause}",
                    (int(archive_after_days), item_id, *params),
                )
            conn.commit()
            return int(cur.rowcount or 0) > 0

    def bump_usage(self, item_ids: List[str], ts_iso: Optional[str] = None) -> None:
        if not item_ids:
            return
        now_iso = ts_iso or datetime.now(timezone.utc).isoformat()
        conn = self._ensure_connection()
        with self._lock:
            for item_id in item_ids:
                conn.execute(
                    """
                    UPDATE items
                    SET usage_count = COALESCE(usage_count, 0) + 1,
                        last_used = ?
                    WHERE id = ?
                    """,
                    (now_iso, item_id),
                )
            conn.commit()

    def related_edges(self, ids: List[str], scope: MemoryScope, limit: int = 30) -> List[Dict[str, str]]:
        if not ids:
            return []
        conn = self._ensure_connection()
        clause, params = self._scope_where(scope)
        placeholders = ",".join(["?"] * len(ids))
        with self._lock:
            rows = conn.execute(
                f"""
                SELECT * FROM edges
                WHERE (src_id IN ({placeholders}) OR dst_id IN ({placeholders})) AND {clause}
                ORDER BY weight DESC
                LIMIT ?
                """,
                (*ids, *ids, *params, int(limit)),
            ).fetchall()
            return [dict(row) for row in rows]
