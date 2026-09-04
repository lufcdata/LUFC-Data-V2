-- Canonical per-match milestone RPC for Match Centre.
-- Keeps the frontend query scoped to a single match and preserves the
-- match_centre_milestones view as the authoritative derived source.

create or replace function public.get_match_centre_milestones(p_match_id integer)
returns table (
  match_id integer,
  milestone_category text,
  person_name text,
  milestone text,
  milestone_number integer,
  category_sort integer,
  milestone_sort integer
)
language sql
stable
security definer
set search_path = public
as $$
  select
    m.match_id,
    m.milestone_category,
    m.person_name,
    m.milestone,
    m.milestone_number,
    m.category_sort,
    m.milestone_sort
  from public.match_centre_milestones m
  where m.match_id = p_match_id
  order by m.milestone_number, m.category_sort, m.milestone_sort, m.person_name;
$$;

revoke all on function public.get_match_centre_milestones(integer) from public;
grant execute on function public.get_match_centre_milestones(integer) to anon, authenticated;
