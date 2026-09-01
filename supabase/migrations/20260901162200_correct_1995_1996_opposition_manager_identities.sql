-- Opposition Managers Gold: canonical identity corrections discovered by fixture-level audit.
-- Raw source strings remain immutable provenance.

insert into public.managerial_people (canonical_name, provenance_note) values
  ('Gary Megson','Canonical correction: Norwich caretaker manager for Leeds fixture on 6 May 1995.'),
  ('Jim Platt','Canonical correction: Darlington manager for both September 1996 League Cup fixtures against Leeds.')
on conflict (canonical_name) do nothing;

-- Norwich, 6 May 1995: source says John Deehan, but Deehan resigned on 9 April.
-- Gary Megson was caretaker manager for the remainder of the season.
update public.matches set opposition_manager_name='Gary Megson' where match_id=3293;
update public.managerial_assignments
set canonical_source_name='Gary Megson', assignment_certainty='confirmed', provenance_status='forensically_validated',
    provenance_note='Raw source names John Deehan, but Deehan resigned on 9 Apr 1995 and Gary Megson took temporary charge. Leeds v Norwich on 6 May 1995 falls within Megson caretaker tenure. Raw source preserved unchanged.'
where match_id=3293;
update public.managerial_assignment_people map
set managerial_person_id=(select managerial_person_id from public.managerial_people where canonical_name='Gary Megson'),
    member_role='manager', role_certainty='confirmed'
from public.managerial_assignments ma, public.managerial_people old_person
where map.managerial_assignment_id=ma.managerial_assignment_id and ma.match_id=3293
  and map.managerial_person_id=old_person.managerial_person_id and old_person.canonical_name='John Deehan';

-- Darlington League Cup, 18 and 25 Sep 1996: source says David Hodgson.
-- Contemporary reporting immediately before the first leg identifies Jim Platt as manager;
-- Darlington history confirms Hodgson did not return until after Platt left in November.
update public.matches set opposition_manager_name='Jim Platt' where match_id in (3358,3360);
update public.managerial_assignments
set canonical_source_name='Jim Platt', assignment_certainty='confirmed', provenance_status='forensically_validated',
    provenance_note='Raw source names David Hodgson, but contemporary reporting on 17 Sep 1996 identifies Jim Platt as Darlington manager immediately before the two-legged League Cup tie against Leeds; Darlington historical accounts confirm Platt remained manager until November 1996, when Hodgson returned. Raw source preserved unchanged.'
where match_id in (3358,3360);
update public.managerial_assignment_people map
set managerial_person_id=(select managerial_person_id from public.managerial_people where canonical_name='Jim Platt'),
    member_role='manager', role_certainty='confirmed'
from public.managerial_assignments ma, public.managerial_people old_person
where map.managerial_assignment_id=ma.managerial_assignment_id and ma.match_id in (3358,3360)
  and map.managerial_person_id=old_person.managerial_person_id and old_person.canonical_name='David Hodgson';
