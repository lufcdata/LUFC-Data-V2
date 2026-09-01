-- Opposition Managers Gold forensic corrections.
-- Preserve matches.opposition_manager_raw as immutable provenance.
-- These fixtures were flattened to one source name but evidence establishes
-- shared first-team managerial authority on the fixture date.

insert into public.managerial_people (canonical_name, provenance_note) values
  ('Jon Rudkin','Added during Opposition Managers Gold audit: Leicester City joint caretaker authority, November 2011'),
  ('Scott Brown','Added during Opposition Managers Gold audit: Rotherham United interim management team, November-December 2023'),
  ('Dan Green','Added during Opposition Managers Gold audit: Rotherham United interim management team, November-December 2023')
on conflict (canonical_name) do nothing;

-- 1 Jan 2001: Middlesbrough — Terry Venables + Bryan Robson.
update public.matches set opposition_manager_authority_type='joint' where match_id=3577;
update public.managerial_assignments
set authority_type='joint', assignment_certainty='confirmed', provenance_status='forensically_validated',
    provenance_note='Middlesbrough fixture on 1 Jan 2001 occurred after Terry Venables joined Bryan Robson as joint manager from 4 Dec 2000. Raw source names Venables only; relational authority records both.'
where match_id=3577;
update public.managerial_assignment_people map
set member_role='joint', role_certainty='confirmed', provenance_note='Confirmed joint manager alongside Bryan Robson.'
from public.managerial_assignments ma
where map.managerial_assignment_id=ma.managerial_assignment_id and ma.match_id=3577
  and map.managerial_person_id=(select managerial_person_id from public.managerial_people where canonical_name='Terry Venables');
insert into public.managerial_assignment_people
  (managerial_assignment_id, managerial_person_id, member_role, role_certainty, provenance_note)
select ma.managerial_assignment_id, mp.managerial_person_id, 'joint', 'confirmed', 'Confirmed joint manager alongside Terry Venables.'
from public.managerial_assignments ma join public.managerial_people mp on mp.canonical_name='Bryan Robson'
where ma.match_id=3577
on conflict (managerial_assignment_id, managerial_person_id) do update
set member_role=excluded.member_role, role_certainty=excluded.role_certainty, provenance_note=excluded.provenance_note;

-- 6 Nov 2011: Leicester City — Mike Stowell + Jon Rudkin joint caretakers.
update public.matches set opposition_manager_authority_type='joint' where match_id=4140;
update public.managerial_assignments
set authority_type='joint', assignment_certainty='confirmed', provenance_status='forensically_validated',
    provenance_note='Leicester fixture on 6 Nov 2011 was managed by joint caretakers Mike Stowell and Jon Rudkin after Sven-Goran Eriksson left. Raw source names Stowell only; relational authority records both.'
where match_id=4140;
update public.managerial_assignment_people map
set member_role='joint', role_certainty='confirmed', provenance_note='Confirmed joint caretaker alongside Jon Rudkin.'
from public.managerial_assignments ma
where map.managerial_assignment_id=ma.managerial_assignment_id and ma.match_id=4140
  and map.managerial_person_id=(select managerial_person_id from public.managerial_people where canonical_name='Mike Stowell');
insert into public.managerial_assignment_people
  (managerial_assignment_id, managerial_person_id, member_role, role_certainty, provenance_note)
select ma.managerial_assignment_id, mp.managerial_person_id, 'joint', 'confirmed', 'Confirmed joint caretaker alongside Mike Stowell.'
from public.managerial_assignments ma join public.managerial_people mp on mp.canonical_name='Jon Rudkin'
where ma.match_id=4140
on conflict (managerial_assignment_id, managerial_person_id) do update
set member_role=excluded.member_role, role_certainty=excluded.role_certainty, provenance_note=excluded.provenance_note;

-- 24 Nov 2023: Rotherham United — three-person interim management team.
update public.matches set opposition_manager_authority_type='joint' where match_id=4724;
update public.managerial_assignments
set authority_type='joint', assignment_certainty='confirmed', provenance_status='forensically_validated',
    provenance_note='Rotherham fixture on 24 Nov 2023 was overseen by an interim management team of Wayne Carlisle, Scott Brown and Dan Green after Matt Taylor was dismissed. Raw source names Carlisle only; relational authority records all three.'
where match_id=4724;
update public.managerial_assignment_people map
set member_role='joint', role_certainty='confirmed', provenance_note='Confirmed member of Rotherham interim management team with Scott Brown and Dan Green.'
from public.managerial_assignments ma
where map.managerial_assignment_id=ma.managerial_assignment_id and ma.match_id=4724
  and map.managerial_person_id=(select managerial_person_id from public.managerial_people where canonical_name='Wayne Carlisle');
insert into public.managerial_assignment_people
  (managerial_assignment_id, managerial_person_id, member_role, role_certainty, provenance_note)
select ma.managerial_assignment_id, mp.managerial_person_id, 'joint', 'confirmed', 'Confirmed member of Rotherham interim management team with Wayne Carlisle.'
from public.managerial_assignments ma join public.managerial_people mp on mp.canonical_name in ('Scott Brown','Dan Green')
where ma.match_id=4724
on conflict (managerial_assignment_id, managerial_person_id) do update
set member_role=excluded.member_role, role_certainty=excluded.role_certainty, provenance_note=excluded.provenance_note;
