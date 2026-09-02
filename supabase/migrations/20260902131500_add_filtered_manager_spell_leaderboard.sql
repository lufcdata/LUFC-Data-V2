-- Presentation/read layer for the Managers page.
-- Preserves the existing aggregated manager leaderboard contract.
-- Numbered manager/head-coach appointments exclude pure caretaker spells,
-- which are displayed as (C), matching the established historical order.

create or replace function public.filtered_manager_spell_leaderboard(
  p_filter text default 'All',
  p_venue text default 'All'
)
returns table(
  manager_spell_id bigint,
  manager_id bigint,
  sequence_order bigint,
  manager_order bigint,
  caretaker_label text,
  manager text,
  status text,
  declared_nation text,
  profile_image_url text,
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
with spell_order as (
  select
    ms.manager_spell_id,
    ms.manager_id,
    ms.legacy_manager_order::bigint as sequence_order,
    case
      when ms.role = 'Caretaker Manager' then null::bigint
      else sum(case when ms.role <> 'Caretaker Manager' then 1 else 0 end)
        over(order by ms.legacy_manager_order, ms.manager_spell_id)::bigint
    end as manager_order,
    case when ms.role = 'Caretaker Manager' then '(C)' else null end as caretaker_label,
    ms.status,
    m.canonical_name as manager,
    m.declared_nation,
    m.profile_image_url
  from public.manager_spells ms
  join public.managers m on m.manager_id = ms.manager_id
),
selected as (
  select
    so.*,
    mt.match_id,
    mt.match_date,
    mt.result,
    mt.leeds_score,
    mt.opponent_score
  from spell_order so
  join public.matches mt on mt.manager_spell_id = so.manager_spell_id
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
  s.manager_spell_id,
  s.manager_id,
  s.sequence_order,
  s.manager_order,
  s.caretaker_label,
  s.manager,
  s.status,
  s.declared_nation,
  s.profile_image_url,
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
group by
  s.manager_spell_id,
  s.manager_id,
  s.sequence_order,
  s.manager_order,
  s.caretaker_label,
  s.manager,
  s.status,
  s.declared_nation,
  s.profile_image_url
order by s.sequence_order desc;
$$;
