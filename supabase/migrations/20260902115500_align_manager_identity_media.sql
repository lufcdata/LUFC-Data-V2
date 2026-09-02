-- LUFC Data V2 manager identity/media sync backup.
-- MANAGERS.csv remains the historical source for declared_nation.
-- The managers table is the canonical live source for declared_nation/profile_image_url.
-- This migration aligns the filtered Managers read contract used by the frontend.

create table if not exists public.manager_media (
  manager_id bigint primary key references public.managers(manager_id) on delete cascade,
  icon_path text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

insert into public.manager_media(manager_id, icon_path)
select manager_id, profile_image_url
from public.managers
where profile_image_url is not null
on conflict(manager_id) do update
set icon_path = excluded.icon_path,
    updated_at = now();

drop function if exists public.filtered_manager_leaderboard(text,text);

create function public.filtered_manager_leaderboard(
  p_filter text default 'All',
  p_venue text default 'All'
)
returns table(
  manager_id bigint,
  manager text,
  full_name text,
  declared_nation text,
  profile_image_url text,
  spells bigint,
  played bigint,
  won bigint,
  drawn bigint,
  lost bigint,
  goals_for bigint,
  goals_against bigint,
  goal_diff bigint,
  win_pct numeric,
  loss_pct numeric,
  first_match date,
  last_match date
)
language sql
stable
as $$
with selected as (
  select
    m.manager_id,
    m.canonical_name,
    m.full_name,
    m.declared_nation,
    m.profile_image_url,
    ms.manager_spell_id as spell_id,
    mt.match_id,
    mt.match_date,
    mt.result,
    mt.leeds_score,
    mt.opponent_score
  from public.managers m
  join public.manager_spells ms on ms.manager_id = m.manager_id
  join public.matches mt on mt.manager_spell_id = ms.manager_spell_id
  left join public.competition_names cn on cn.competition_name_id = mt.competition_name_id
  where
    (
      p_venue = 'All'
      or (p_venue = 'Home' and mt.venue_type = 'H')
      or (p_venue = 'Away' and mt.venue_type = 'A')
      or (p_venue = 'Neutral' and mt.venue_type = 'N')
    )
    and (
      p_filter = 'All'
      or (p_filter = 'League' and coalesce(cn.display_name, mt.source_comp) in ('Division One','Division Two','Division Three','Championship','League One','Premier League'))
      or (p_filter = 'Premier League' and coalesce(cn.display_name, mt.source_comp) = 'Premier League')
      or (p_filter = 'FA Cup' and coalesce(cn.display_name, mt.source_comp) = 'FA Cup')
      or (p_filter = 'League Cup' and coalesce(cn.display_name, mt.source_comp) in ('League Cup','EFL Cup'))
      or (p_filter = 'Europe' and coalesce(cn.display_name, mt.source_comp) in ('European Cup','European Cup Winners Cup','European Cup Winners'' Cup','Inter-Cities Fairs Cup','UEFA Cup','UEFA Champions League','UEFA Europa League'))
    )
)
select
  s.manager_id,
  s.canonical_name,
  s.full_name,
  s.declared_nation,
  max(s.profile_image_url),
  count(distinct s.spell_id),
  count(s.match_id),
  count(*) filter(where s.result = 'Won'),
  count(*) filter(where s.result = 'Draw'),
  count(*) filter(where s.result = 'Lost'),
  coalesce(sum(s.leeds_score), 0),
  coalesce(sum(s.opponent_score), 0),
  coalesce(sum(s.leeds_score), 0) - coalesce(sum(s.opponent_score), 0),
  round(100.0 * count(*) filter(where s.result = 'Won') / nullif(count(s.match_id), 0), 1),
  round(100.0 * count(*) filter(where s.result = 'Lost') / nullif(count(s.match_id), 0), 1),
  min(s.match_date),
  max(s.match_date)
from selected s
group by s.manager_id, s.canonical_name, s.full_name, s.declared_nation;
$$;
