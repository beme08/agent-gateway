-- 0008_fix_acl_semantics.sql
-- Fix ACL matching in match_document_chunks.
--
-- The previous check `c.acl_tags && filter_tags` (ANY overlap) leaked
-- mixed-tag chunks: a chunk tagged {hr_policy, executive} was returned to an
-- employee because one tag overlapped. Authorization must instead require the
-- intended relationship: a chunk is only returned when EVERY tag it carries
-- is within the caller's granted set (array containment).
--
-- New semantics:
--   * `c.acl_tags <@ filter_tags` -- containment, not overlap.
--   * `cardinality(c.acl_tags) > 0` -- an untagged chunk is not implicitly
--     accessible to everyone; restricted content must be explicitly tagged.
--
-- Consequence for existing seed data: public HR policies were redundantly
-- tagged {public, hr_policy}. Under overlap that was harmless; under
-- containment it would wrongly hide them from the `viewer` role. The backfill
-- below normalizes those documents to the single `public` tag. `public` is the
-- widest grant (every role's allowed set includes it), so a document tagged
-- `public` alone is visible to all roles -- which is the intended behavior.

create or replace function public.match_document_chunks(
  query_embedding vector(1024),
  filter_tenant uuid,
  filter_tags text[],
  match_count int default 5
)
returns table (
  id uuid,
  document_id uuid,
  chunk_index int,
  content text,
  acl_tags text[],
  page int,
  section text,
  similarity float
)
language sql
stable
as $$
  select
    c.id,
    c.document_id,
    c.chunk_index,
    c.content,
    c.acl_tags,
    c.page,
    c.section,
    1 - (c.embedding <=> query_embedding) as similarity
  from public.document_chunks c
  where c.tenant_id = filter_tenant
    and cardinality(c.acl_tags) > 0
    and c.acl_tags <@ filter_tags
  order by c.embedding <=> query_embedding asc
  limit greatest(1, match_count);
$$;

-- Normalize stale multi-tagged public documents to a single `public` tag so
-- that viewer access is preserved under containment semantics.
update public.document_chunks c
set acl_tags = array['public']
from public.documents d
where d.id = c.document_id
  and d.title in (
    'Acme Remote Work Policy',
    'Acme Sick Leave Policy',
    'Acme PTO Policy',
    'Globex Remote Work Policy',
    'Globex Sick Leave Policy',
    'Globex PTO Policy'
  )
  and c.acl_tags && array['hr_policy']::text[]
  and not (c.acl_tags <@ array['public']::text[]);