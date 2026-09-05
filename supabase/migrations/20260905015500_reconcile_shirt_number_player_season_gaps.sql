-- Reconcile canonical post-1993 player-season shirt-number gaps found by
-- comparing player_matches to official seasonal squad-number assignments.
-- IMPORTANT: use matches.season_id for season membership. Do not infer a
-- football season from calendar dates: the delayed 2019/20 season continued
-- into July 2020.

insert into public.player_season_squad_numbers
  (season_id, player_id, squad_number, assignment_status, notes)
select
  s.season_id,
  v.player_id,
  v.squad_number::smallint,
  'reconciled_external_source',
  v.notes
from (values
  (1998, 499::bigint, 7,  'Reconciled player-season gap; FootballSquads 1998/99 lists Lee Sharpe as #7.'),
  (2000, 527::bigint, 12, 'Reconciled player-season gap; 2000/01 season squad records list Darren Huckerby as #12.'),
  (2008, 655::bigint, 13, 'Reconciled player-season gap; FootballSquads 2008/09 and Transfermarkt list Mike Grella as #13.'),
  (2009, 647::bigint, 32, 'Reconciled player-season gap; 2009/10 season squad records list Aidan White as #32.'),
  (2009, 663::bigint, 27, 'Reconciled player-season gap; 2009/10 season squad records list Davide Somma as #27.'),
  (2009, 646::bigint, 21, 'Reconciled player-season gap; 2009/10 season squad records list Enoch Showunmi as #21.'),
  (2009, 673::bigint, 24, 'Reconciled player-season gap; 2009/10 season squad records list Sanchez Watt as #24.'),
  (2010, 647::bigint, 32, 'Reconciled player-season gap; 2010/11 squad records list Aidan White as #32.'),
  (2010, 685::bigint, 40, 'Reconciled player-season gap; Leeds-era sources list Andy O’Brien as #40 in 2010/11.'),
  (2010, 625::bigint, 19, 'Reconciled player-season gap; FootballSquads/ESPN list Ben Parker as #19 in 2010/11.'),
  (2013, 731::bigint, 22, 'Reconciled player-season gap; 2013/14 squad records list Scott Wootton as #22.'),
  (2015, 771::bigint, 37, 'Reconciled player-season gap; FootballSquads/ESPN list Ronaldo Vieira as #37 in 2015/16.'),
  (2020, 809::bigint, 3,  'Reconciled player-season gap; Leeds United official 2020/21 squad-number announcement lists Barry Douglas as #3.'),
  (2020, 828::bigint, 44, 'Reconciled player-season gap; Leeds United official 2020/21 squad-number announcement lists Mateusz Bogusz as #44.'),
  (2020, 832::bigint, 36, 'Reconciled player-season gap; Leeds United official 2020/21 squad-number announcement lists Robbie Gotts as #36.'),
  (2021, 848::bigint, 37, 'Reconciled player-season gap; 2021/22 Leeds team sheets and squad records list Cody Drameh as #37.'),
  (2021, 824::bigint, 17, 'Reconciled player-season gap; 2021/22 Leeds squad/team-sheet records list Helder Costa as #17.')
) as v(start_year, player_id, squad_number, notes)
join public.seasons s on s.start_year = v.start_year
where not exists (
  select 1
  from public.player_season_squad_numbers ps
  where ps.season_id = s.season_id
    and ps.player_id = v.player_id
);
