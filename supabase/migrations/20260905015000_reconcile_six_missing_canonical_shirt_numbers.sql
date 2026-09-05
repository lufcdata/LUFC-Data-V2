-- Reconcile six canonical Leeds appearance-makers missing from the supplied fixed-era CSV.
-- The 902-player identity boundary is unchanged.
-- Numbers were independently verified against historical squad/team-sheet sources.

insert into public.player_season_squad_numbers
  (season_id, player_id, squad_number, assignment_status, notes)
select
  s.season_id,
  v.player_id,
  v.squad_number::smallint,
  'listed',
  v.notes
from (values
  ('2003/2004', 559::bigint, 15, 'Reconciled canonical gap: Steven Caldwell wore #15 for Leeds in 2003/04; verified against 11v11 and Transfermarkt.'),
  ('2009/2010', 665::bigint, 15, 'Reconciled canonical gap: Sam Vokes wore #15 for Leeds in 2009/10; verified against 11v11 and season squad records.'),
  ('2011/2012', 698::bigint, 7, 'Reconciled canonical gap: Mika Väyrynen wore #7 for Leeds in 2011/12; verified against FootballSquads, Transfermarkt and match team sheets.'),
  ('2011/2012', 701::bigint, 17, 'Reconciled canonical gap: Andros Townsend wore #17 for Leeds in 2011/12; verified against FootballSquads, Transfermarkt and match team sheets.'),
  ('2011/2012', 705::bigint, 33, 'Reconciled canonical gap: defender Paul Robinson wore #33 for Leeds in 2011/12; verified against FootballSquads and match team sheets.'),
  ('2013/2014', 733::bigint, 24, 'Reconciled canonical gap: Marius Zaliukas wore #24 for Leeds in 2013/14; verified against contemporary season squad records.')
) as v(season_name, player_id, squad_number, notes)
join public.seasons s
  on s.display_name = v.season_name
where not exists (
  select 1
  from public.player_season_squad_numbers ps
  where ps.season_id = s.season_id
    and ps.player_id = v.player_id
);
