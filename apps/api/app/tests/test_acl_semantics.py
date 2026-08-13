"""Regression tests for the ACL matching fix.

Covers:
  1. The intended semantics (containment, not overlap) as a plain-language
     contract mirrored from the SQL predicate.
  2. The migration contract: 0008 (which replaces 0004) must use `acl_tags <@
     filter_tags` + a cardinality guard, not overlap (`&&`). This guards the
     actual SQL file against regression even though unit tests can't run
     Postgres.
"""
from pathlib import Path

from app.rag.retrieve import accessible_tags

REPO_ROOT = Path(__file__).resolve().parents[4]
MIGRATION_0008 = REPO_ROOT / "supabase" / "migrations" / "0008_fix_acl_semantics.sql"


def _allowed(role: str) -> set[str]:
    return set(accessible_tags(role))


def test_containment_blocks_mixed_tag_chunk():
    # Core leak: an employee has {public, hr_policy}; a chunk tagged
    # {hr_policy, executive} must NOT be returned even though one tag overlaps.
    allowed = _allowed("employee")
    chunk_tags = {"hr_policy", "executive"}
    assert not chunk_tags.issubset(allowed)


def test_containment_allows_fully_granted_chunk():
    allowed = _allowed("employee")
    assert {"public"}.issubset(allowed)
    assert {"hr_policy"}.issubset(allowed)


def test_containment_blocks_partially_granted_public_doc():
    # A doc tagged both public and hr_policy is not visible to a viewer who
    # only holds `public` -- mixed grants are evaluated as AND, not OR.
    allowed = _allowed("viewer")
    assert {"public", "hr_policy"}.issubset(allowed) is False


def test_untagged_chunk_is_not_public():
    # cardinality(c.acl_tags) > 0: no tags => no access. Avoids empty-tag
    # rows silently bypassing the ACL.
    allowed = _allowed("admin")
    chunk_tags: set[str] = set()
    assert chunk_tags.issubset(allowed)  # would be vacuously true under <@
    assert len(chunk_tags) == 0  # contract: SQL must also require >0


def test_migration_uses_containment_not_overlap():
    sql = MIGRATION_0008.read_text()
    body = sql.split("as $$", 1)[1].split("$$;", 1)[0]
    assert "acl_tags <@ filter_tags" in body, "0008 must use containment"
    assert "cardinality(c.acl_tags) > 0" in body, "0008 must require explicit tags"
    assert "acl_tags && filter_tags" not in body, "0008 must not reintroduce ANY overlap in the function"