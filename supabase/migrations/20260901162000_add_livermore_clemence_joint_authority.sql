-- Opposition Managers Gold correction
-- Tottenham Hotspur 1992-93: Doug Livermore + Ray Clemence shared first-team authority.
-- Raw source strings remain unchanged.

insert into public.managerial_people (canonical_name, provenance_note)
values ('Ray Clemence','Added during Opposition Managers Gold audit after Tottenham 1992-93 co-manager evidence')
on conflict (canonical_name) do nothing;

update public.matches
set opposition_manager_authority_type='joint'
where match_id in (3150,3187);

update public.managerial_assignments
set authority_type='joint',
    assignment_certainty='confirmed',
    provenance_status='forensically_validated',
    provenance_note='Tottenham 1992-93 first-team authority was shared by Doug Livermore and Ray Clemence; both Leeds fixtures fall inside the co-manager period.'
where match_id in (3150,3187);

update public.managerial_assignment_people map
set member_role='joint',
    role_certainty='confirmed',
    provenance_note='Doug Livermore co-managed Tottenham with Ray Clemence during 1992-93.'
from public.managerial_assignments ma, public.managerial_people mp
where map.managerial_assignment_id=ma.managerial_assignment_id
  and map.managerial_person_id=mp.managerial_person_id
  and ma.match_id in (3150,3187)
  and mp.canonical_name='Doug Livermore';

insert into public.managerial_assignment_people
  (managerial_assignment_id, managerial_person_id, member_role, role_certainty, provenance_note)
select ma.managerial_assignment_id,
       mp.managerial_person_id,
       'joint',
       'confirmed',
       'Ray Clemence co-managed Tottenham with Doug Livermore during 1992-93.'
from public.managerial_assignments ma
cross join public.managerial_people mp
where ma.match_id in (3150,3187)
  and mp.canonical_name='Ray Clemence'
on conflict (managerial_assignment_id, managerial_person_id) do nothing;
