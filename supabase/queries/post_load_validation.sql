-- LUFC Data V2 post-load integrity gates.
-- Each query must return the expected value before a database load is signed off.

-- Core snapshot counts (audited 2026-08-31).
select 'matches' as check_name, count(*) as actual, 4856 as expected from matches;
select 'players' as check_name, count(*) as actual, 902 as expected from players;
select 'manager_spells' as check_name, count(*) as actual, 57 as expected from manager_spells;
select 'goals' as check_name, count(*) as actual, 7282 as expected from goals;
select 'player_matches' as check_name, count(*) as actual, 58527 as expected from player_matches;
select 'starts' as check_name, count(*) filter (where started) as actual, 53416 as expected from player_matches;
select 'substitute_appearances' as check_name, count(*) filter (where substitute) as actual, 5111 as expected from player_matches;
select 'opponent_own_goals' as check_name, count(*) filter (where is_own_goal) as actual, 153 as expected from goals;

-- Referential/invariant checks: all must return zero.
select 'duplicate_match_ids' as check_name, count(*) as failures from (select match_id from matches group by match_id having count(*)>1) q;
select 'duplicate_player_match' as check_name, count(*) as failures from (select match_id,player_id from player_matches group by match_id,player_id having count(*)>1) q;
select 'invalid_start_sub_state' as check_name, count(*) as failures from player_matches where started=substitute;
select 'goal_without_match' as check_name, count(*) as failures from goals g left join matches m on m.match_id=g.match_id where m.match_id is null;
select 'appearance_without_player' as check_name, count(*) as failures from player_matches pm left join players p on p.player_id=pm.player_id where p.player_id is null;

-- Same-date double headers must remain distinct.
select match_date, array_agg(match_id order by match_id) as match_ids, count(*) as matches_on_date
from matches where match_date in (date '1920-09-11',date '1920-09-25')
group by match_date order by match_date;

-- Confirmed correction regression checks.
select 'ellson_leicester_match_6' as check_name, count(*) as actual, 1 as expected
from goals g join matches m using(match_id)
where g.legacy_goal_number=10 and g.match_id=6 and m.match_date=date '1920-09-11';

select 'becchio_millwall_4011' as check_name, count(*) as actual, 1 as expected
from goals g join matches m using(match_id)
where g.legacy_goal_number=6046 and g.match_id=4011 and m.match_date=date '2009-05-14';

select 'hankin_aston_villa_away' as check_name, count(*) as actual, 1 as expected
from goals g join matches m using(match_id)
where g.legacy_goal_number=3868 and m.match_date=date '1978-04-26' and m.venue_type='A';

-- Paul Robinson identities must remain separate.
select display_name, legacy_player_id, date_of_birth
from players
where legacy_player_id in (518,705)
order by legacy_player_id;
