-- 0004_match_chunks.sql
-- ACL-filtered vector retrieval. Only returns chunks whose acl_tags overlap
-- the caller's allowed tags. Restricted tags are physically excluded.

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
    and c.acl_tags && filter_tags
  order by c.embedding <=> query_embedding asc
  limit greatest(1, match_count);
$$;
