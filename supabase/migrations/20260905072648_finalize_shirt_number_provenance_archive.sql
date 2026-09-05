-- Finalize and validate the raw shirt-number provenance archive after the authoritative CSV import.
-- Raw CSV rows are data-imported into shirt_number_source_rows; this migration resolves canonical IDs, refreshes source links, removes stale audit artifacts, and hard-validates the imported source fingerprints.

update public.shirt_number_source_rows
set source_file_name = 'leeds_united_squad_numbers_1993-94_to_2026-27 - leeds_united_squad_numbers_1991-92_to_2025-26.csv)(1).csv'
where source_file_name = 'leeds_united_squad_numbers_1993-94_to_2026-27 - leeds_united_squad_numbers_1991-92_to_2025-26.csv).csv';

update public.shirt_number_source_rows s
set season_id = se.season_id
from public.seasons se
where s.source_file_name = 'leeds_united_squad_numbers_1993-94_to_2026-27 - leeds_united_squad_numbers_1991-92_to_2025-26.csv)(1).csv'
  and se.start_year = substring(s.source_season from 1 for 4)::integer;

update public.shirt_number_source_rows s
set player_id = p.player_id
from public.players p
where s.source_file_name = 'leeds_united_squad_numbers_1993-94_to_2026-27 - leeds_united_squad_numbers_1991-92_to_2025-26.csv)(1).csv'
  and p.display_name = s.source_player_name;

update public.shirt_number_source_rows s
set player_id = a.player_id
from public.player_source_aliases a
where s.source_file_name = 'leeds_united_squad_numbers_1993-94_to_2026-27 - leeds_united_squad_numbers_1991-92_to_2025-26.csv)(1).csv'
  and s.player_id is null
  and a.source_name = 'shirt_numbers_1993_94_to_2026_27'
  and a.source_player_name = s.source_player_name;

update public.shirt_number_source_rows
set resolution_status = case when season_id is null then 'unresolved_season' when player_id is null then 'excluded_noncanonical_player' else 'resolved_canonical' end,
    resolution_notes = case when season_id is null then 'Source season did not resolve to canonical season' when player_id is null then 'Source player is outside the closed 902-player canonical universe' else null end
where source_file_name = 'leeds_united_squad_numbers_1993-94_to_2026-27 - leeds_united_squad_numbers_1991-92_to_2025-26.csv)(1).csv';

update public.shirt_number_source_rows s
set season_id = se.season_id
from public.seasons se
where s.source_file_name = 'leeds_united_1991-92_every_match_shirt_number(1).csv'
  and se.start_year = substring(s.source_season from 1 for 4)::integer;

update public.shirt_number_source_rows s
set player_id = p.player_id
from public.players p
where s.source_file_name = 'leeds_united_1991-92_every_match_shirt_number(1).csv'
  and p.display_name = s.source_player_name;

update public.shirt_number_source_rows s
set match_id = m.match_id
from public.matches m
where s.source_file_name = 'leeds_united_1991-92_every_match_shirt_number(1).csv'
  and m.season_id = s.season_id
  and m.match_date = s.source_match_date;

update public.shirt_number_source_rows
set resolution_status = case when season_id is null then 'unresolved_season' when match_id is null then 'unresolved_match' when player_id is null then 'excluded_noncanonical_player' else 'resolved_canonical' end,
    resolution_notes = case when season_id is null then 'Source season did not resolve to canonical season' when match_id is null then 'Source match did not resolve to canonical match' when player_id is null then 'Source player is outside the closed 902-player canonical universe' else null end
where source_file_name = 'leeds_united_1991-92_every_match_shirt_number(1).csv';

update public.player_match_shirt_numbers p
set source_row_id = s.source_row_id
from public.shirt_number_source_rows s
where s.era = 'match_by_match' and s.resolution_status = 'resolved_canonical' and p.match_id = s.match_id and p.player_id = s.player_id and p.shirt_number = s.shirt_number;

update public.player_season_squad_numbers p
set source_row_id = s.source_row_id
from public.shirt_number_source_rows s
where s.source_file_name = 'leeds_united_squad_numbers_1993-94_to_2026-27 - leeds_united_squad_numbers_1991-92_to_2025-26.csv)(1).csv'
  and s.resolution_status = 'resolved_canonical' and p.season_id = s.season_id and p.player_id = s.player_id and p.squad_number is not distinct from s.shirt_number;

update public.player_season_squad_numbers p
set source_row_id = s.source_row_id
from public.shirt_number_source_rows s
where s.source_file_name = 'supplemental_external_reconciliation' and s.resolution_status = 'supplemental_verified'
  and p.season_id = s.season_id and p.player_id = s.player_id and p.squad_number is not distinct from s.shirt_number and p.source_row_id is null;

delete from public.shirt_number_source_rows
where source_file_name = 'canonical_assignment_audit'
  and not exists (select 1 from public.player_season_squad_numbers p where p.source_row_id = public.shirt_number_source_rows.source_row_id);

do $$
declare v bigint; h text;
begin
  select count(*) into v from public.players; if v <> 902 then raise exception 'Expected 902 canonical players, found %', v; end if;
  select count(*) into v from public.shirt_number_source_rows; if v <> 2757 then raise exception 'Expected 2757 shirt-number provenance rows, found %', v; end if;
  select count(*) into v from public.shirt_number_source_rows where resolution_status is null or resolution_status like 'unresolved%'; if v <> 0 then raise exception 'Expected zero unresolved shirt-number provenance rows, found %', v; end if;
  select count(*) into v from public.player_match_shirt_numbers where source_row_id is not null; if v <> 1409 then raise exception 'Expected 1409/1409 match-level canonical rows linked to provenance, found %', v; end if;
  select count(*) into v from public.player_season_squad_numbers where source_row_id is not null; if v <> 1152 then raise exception 'Expected 1152/1152 fixed-era canonical rows linked to provenance, found %', v; end if;

  select md5(string_agg(source_season||chr(31)||coalesce(shirt_number_raw,'')||chr(31)||source_player_name||chr(31)||coalesce(source_status,'')||chr(31)||coalesce(source_notes,'')||chr(31)||coalesce(source_name,''), chr(30) order by source_row_number)) into h from public.shirt_number_source_rows where source_file_name = 'leeds_united_squad_numbers_1993-94_to_2026-27 - leeds_united_squad_numbers_1991-92_to_2025-26.csv)(1).csv';
  if h <> '07027ac80da601f2ee4f2371b41265f9' then raise exception 'Fixed-era raw-field fingerprint mismatch: %', h; end if;

  select md5(string_agg(coalesce(source_payload->>'season','')||chr(31)||coalesce(source_payload->>'date','')||chr(31)||coalesce(source_payload->>'competition','')||chr(31)||coalesce(source_payload->>'competition_match_number','')||chr(31)||coalesce(source_payload->>'opponent','')||chr(31)||coalesce(source_payload->>'venue','')||chr(31)||coalesce(source_payload->>'result_leeds_first','')||chr(31)||coalesce(source_payload->>'shirt_number','')||chr(31)||coalesce(source_payload->>'player','')||chr(31)||coalesce(source_payload->>'role','')||chr(31)||coalesce(source_payload->>'substitute_status','')||chr(31)||coalesce(source_payload->>'numbering_type','')||chr(31)||coalesce(source_payload->>'source',''), chr(30) order by source_row_number)) into h from public.shirt_number_source_rows where source_file_name = 'leeds_united_1991-92_every_match_shirt_number(1).csv';
  if h <> 'd1359efc14a4a55db5bbacf8ea787f11' then raise exception '1991/92 raw-field fingerprint mismatch: %', h; end if;

  select md5(string_agg(coalesce(source_payload->>'season','')||chr(31)||coalesce(source_payload->>'date','')||chr(31)||coalesce(source_payload->>'competition','')||chr(31)||coalesce(source_payload->>'competition_match_number','')||chr(31)||coalesce(source_payload->>'opponent','')||chr(31)||coalesce(source_payload->>'venue','')||chr(31)||coalesce(source_payload->>'result_leeds_first','')||chr(31)||coalesce(source_payload->>'shirt_number','')||chr(31)||coalesce(source_payload->>'player','')||chr(31)||coalesce(source_payload->>'role','')||chr(31)||coalesce(source_payload->>'substitute_status','')||chr(31)||coalesce(source_payload->>'numbering_type','')||chr(31)||coalesce(source_payload->>'source',''), chr(30) order by source_row_number)) into h from public.shirt_number_source_rows where source_file_name = 'leeds_united_1992-93_every_match_shirt_number(1)(1).csv';
  if h <> '2ae073f1c188f8fb5ccc8a46689dc3f9' then raise exception '1992/93 raw-field fingerprint mismatch: %', h; end if;
end $$;
