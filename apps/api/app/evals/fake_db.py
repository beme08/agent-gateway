"""In-memory fake Supabase client for deterministic end-to-end evals.

Implements the subset of the supabase-py fluent API the gateway uses:
insert / select / update / delete-by-filters / order / limit / single / rpc.
`match_document_chunks` is implemented as deterministic keyword-overlap
ranking with tenant + ACL-tag filtering (no embeddings required).
"""
from __future__ import annotations

import re
import uuid


def _uuid() -> str:
    return str(uuid.uuid4())


class FakeResult:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, store: FakeStore, table: str):
        self._store = store
        self._table = table
        self._filters: list[tuple[str, str, object]] = []
        self._order: tuple[str, bool] | None = None
        self._limit: int | None = None
        self._single = False
        self._payload: object = None
        self._mode = "select"

    # ---- builders ----------------------------------------------------------

    def select(self, cols: str = "*", **_kwargs) -> FakeQuery:
        self._mode = "select"
        return self

    def insert(self, payload) -> FakeQuery:
        self._mode = "insert"
        self._payload = payload
        return self

    def update(self, fields: dict) -> FakeQuery:
        self._mode = "update"
        self._payload = fields
        return self

    def delete(self) -> FakeQuery:
        self._mode = "delete"
        return self

    def eq(self, col: str, val) -> FakeQuery:
        self._filters.append((col, "eq", val))
        return self

    def in_(self, col: str, vals) -> FakeQuery:
        self._filters.append((col, "in", vals))
        return self

    def order(self, col: str, desc: bool = False) -> FakeQuery:
        self._order = (col, desc)
        return self

    def limit(self, n: int) -> FakeQuery:
        self._limit = n
        return self

    def single(self) -> FakeQuery:
        self._single = True
        return self

    def execute(self) -> FakeResult:
        rows = self._store.tables.setdefault(self._table, [])

        if self._mode == "insert":
            payload = self._payload if isinstance(self._payload, list) else [self._payload]
            out = []
            for row in payload:
                new = dict(row)
                new.setdefault("id", _uuid())
                new.setdefault("created_at", "2026-08-21T00:00:00Z")
                rows.append(new)
                out.append(new)
            return FakeResult(out)

        matched = [r for r in rows if self._matches(r)]
        if self._mode == "update":
            for r in matched:
                r.update(self._payload)
            return FakeResult([dict(r) for r in matched])
        if self._mode == "delete":
            self._store.tables[self._table] = [r for r in rows if not self._matches(r)]
            return FakeResult([])

        # select
        if self._order:
            col, desc = self._order
            matched = sorted(matched, key=lambda r: str(r.get(col, "")), reverse=desc)
        if self._limit is not None:
            matched = matched[: self._limit]
        if self._single:
            if not matched:
                raise RuntimeError(f"no row in {self._table} for {self._filters}")
            return FakeResult(dict(matched[0]))
        return FakeResult([dict(r) for r in matched])

    def _matches(self, row: dict) -> bool:
        for col, op, val in self._filters:
            if op == "eq" and row.get(col) != val:
                return False
            if op == "in" and row.get(col) not in val:
                return False
        return True


class FakeStore:
    """Table store + helpers used by the eval harness."""

    def __init__(self) -> None:
        self.tables: dict[str, list[dict]] = {}

    # ---- supabase-style entrypoint ------------------------------------------

    def table(self, table: str) -> FakeQuery:
        return FakeQuery(self, table)

    def rpc(self, name: str, params: dict) -> FakeQuery:
        raise NotImplementedError(f"rpc '{name}' not faked; harness patches rag.search")

    # ---- helpers -------------------------------------------------------------

    def seed(self, table: str, rows: list[dict]) -> None:
        self.tables.setdefault(table, []).extend(rows)

    def all(self, table: str) -> list[dict]:
        return self.tables.get(table, [])

    def find(self, table: str, **eq) -> list[dict]:
        out = self.tables.get(table, [])
        for k, v in eq.items():
            out = [r for r in out if r.get(k) == v]
        return out


def keyword_search(store: FakeStore, tenant_id: str, role: str, query: str,
                   top_k: int = 5, tags_override: list[str] | None = None):
    """Deterministic ACL-filtered keyword retrieval replacing rag.search."""
    from app.rag.retrieve import accessible_tags

    allowed = set(tags_override if tags_override is not None else accessible_tags(role))
    words = set(re.findall(r"[a-z0-9]+", query.lower()))
    scored = []
    for chunk in store.all("document_chunks"):
        chunk = dict(chunk)
        chunk.setdefault("id", _uuid())
        if chunk.get("tenant_id") != tenant_id:
            continue
        if not (allowed & set(chunk.get("acl_tags") or [])):
            continue
        content_words = set(re.findall(r"[a-z0-9]+", chunk.get("content", "").lower()))
        overlap = len(words & content_words)
        if words and overlap == 0:
            continue
        scored.append((overlap, {
            "id": chunk["id"],
            "document_id": chunk["document_id"],
            "chunk_index": chunk.get("chunk_index", 0),
            "content": chunk.get("content", ""),
            "page": chunk.get("page"),
            "section": chunk.get("section"),
            "acl_tags": chunk.get("acl_tags", []),
            "similarity": round(overlap / (len(words) or 1), 4),
        }))
    scored.sort(key=lambda pair: -pair[0])
    return [c for _, c in scored[:top_k]]
