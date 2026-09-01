-- Synchronize opposition-manager corrections already forensically established in the live database.
-- Idempotent: joins use canonical names and match IDs, never generated identity values.

insert into managerial_people (canonical_name)
values
  ('Colin Lee'),
  ('Iffy Onuora'),
  ('Mick Docherty'),
  ('Richard Shaw'),
  ('Colin West'),
  ('John Pemberton'),
  ('Wade Elliott')
on conflict (canonical_name) do nothing;

-- Millwall 2005/06: source remained stale on Dennis Wise after his May 2005 departure.
update matches
set opposition_manager_name = 'Colin Lee'
where match_id in (3796, 3818);

update managerial_assignments
set canonical_source_name = 'Colin Lee',
    authority_type = 'individual',
    assignment_certainty = 'confirmed',
    provenance_status = 'forensically_validated',
    provenance_note = 'Colin Lee confirmed as Millwall manager for the 2005/06 Leeds fixture; raw source Dennis Wise is preserved as immutable provenance. Wise resigned in May 2005 and Lee was appointed in July 2005.'
where match_id in (3796, 3818);

delete from managerial_assignment_people map
using managerial_assignments ma
where map.managerial_assignment_id = ma.managerial_assignment_id
  and ma.match_id in (3796, 3818);

insert into managerial_assignment_people (managerial_assignment_id, managerial_person_id, member_role, role_certainty, provenance_note)
select ma.managerial_assignment_id, mp.managerial_person_id, 'manager', 'confirmed', 'Canonical fixture authority after forensic correction.'
from managerial_assignments ma
join managerial_people mp on mp.canonical_name = 'Colin Lee'
where ma.match_id in (3796, 3818)
on conflict (managerial_assignment_id, managerial_person_id) do update
set member_role = excluded.member_role,
    role_certainty = excluded.role_certainty,
    provenance_note = excluded.provenance_note;

-- Gillingham 29 Sep 2007: Iffy Onuora and Mick Docherty were joint caretakers.
update matches
set opposition_manager_authority_type = 'joint'
where match_id = 3909;

update managerial_assignments
set authority_type = 'joint',
    assignment_certainty = 'confirmed',
    provenance_status = 'forensically_validated',
    provenance_note = 'Iffy Onuora and Mick Docherty confirmed as joint caretakers for Gillingham v Leeds on 29 Sep 2007; raw source naming Onuora alone is preserved.'
where match_id = 3909;

insert into managerial_assignment_people (managerial_assignment_id, managerial_person_id, member_role, role_certainty, provenance_note)
select ma.managerial_assignment_id, mp.managerial_person_id, 'joint caretaker', 'confirmed', 'Shared first-team authority confirmed for this fixture.'
from managerial_assignments ma
join managerial_people mp on mp.canonical_name in ('Iffy Onuora','Mick Docherty')
where ma.match_id = 3909
on conflict (managerial_assignment_id, managerial_person_id) do update
set member_role = excluded.member_role,
    role_certainty = excluded.role_certainty,
    provenance_note = excluded.provenance_note;

-- Millwall 27 Oct 2007: Richard Shaw and Colin West were joint caretakers.
update matches
set opposition_manager_authority_type = 'joint'
where match_id = 3915;

update managerial_assignments
set authority_type = 'joint',
    assignment_certainty = 'confirmed',
    provenance_status = 'forensically_validated',
    provenance_note = 'Richard Shaw and Colin West confirmed as joint caretakers for Millwall v Leeds on 27 Oct 2007; raw source naming Shaw alone is preserved.'
where match_id = 3915;

insert into managerial_assignment_people (managerial_assignment_id, managerial_person_id, member_role, role_certainty, provenance_note)
select ma.managerial_assignment_id, mp.managerial_person_id, 'joint caretaker', 'confirmed', 'Shared first-team authority confirmed for this fixture.'
from managerial_assignments ma
join managerial_people mp on mp.canonical_name in ('Richard Shaw','Colin West')
where ma.match_id = 3915
on conflict (managerial_assignment_id, managerial_person_id) do update
set member_role = excluded.member_role,
    role_certainty = excluded.role_certainty,
    provenance_note = excluded.provenance_note;

-- Bristol City 23 Jan 2016: John Pemberton and Wade Elliott were joint interim managers.
update matches
set opposition_manager_authority_type = 'joint'
where match_id = 4355;

update managerial_assignments
set authority_type = 'joint',
    assignment_certainty = 'confirmed',
    provenance_status = 'forensically_validated',
    provenance_note = 'John Pemberton and Wade Elliott confirmed as joint interim managers for Leeds v Bristol City on 23 Jan 2016; raw source naming Pemberton alone is preserved.'
where match_id = 4355;

insert into managerial_assignment_people (managerial_assignment_id, managerial_person_id, member_role, role_certainty, provenance_note)
select ma.managerial_assignment_id, mp.managerial_person_id, 'joint interim manager', 'confirmed', 'Shared first-team authority confirmed for this fixture.'
from managerial_assignments ma
join managerial_people mp on mp.canonical_name in ('John Pemberton','Wade Elliott')
where ma.match_id = 4355
on conflict (managerial_assignment_id, managerial_person_id) do update
set member_role = excluded.member_role,
    role_certainty = excluded.role_certainty,
    provenance_note = excluded.provenance_note;
