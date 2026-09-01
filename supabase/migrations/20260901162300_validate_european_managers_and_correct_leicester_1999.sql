-- Opposition Managers Gold audit: validate selected European fixtures and correct Leicester 26 Dec 1999.
-- Golden rule: matches.opposition_manager_raw remains immutable provenance.

-- 26 Dec 1999 Leeds v Leicester City: raw source names Graham Taylor, but Martin O'Neill was Leicester manager.
update public.matches
set opposition_manager_name='Martin O''Neill'
where match_id=3519;

update public.managerial_assignments
set canonical_source_name='Martin O''Neill',
    assignment_certainty='confirmed',
    provenance_status='forensically_validated',
    provenance_note='Leicester City fixture on 26 Dec 1999 was managed by Martin O''Neill. The raw source names Graham Taylor, but Leicester season records and manager-match chronology place O''Neill in charge for this fixture; raw source preserved unchanged.'
where match_id=3519;

delete from public.managerial_assignment_people map
using public.managerial_assignments ma, public.managerial_people mp
where map.managerial_assignment_id=ma.managerial_assignment_id
  and ma.match_id=3519
  and map.managerial_person_id=mp.managerial_person_id
  and mp.canonical_name='Graham Taylor';

insert into public.managerial_assignment_people
  (managerial_assignment_id, managerial_person_id, member_role, role_certainty, provenance_note)
select ma.managerial_assignment_id, mp.managerial_person_id, 'manager', 'confirmed',
       'Confirmed Leicester City manager for 26 Dec 1999 fixture; raw source incorrectly names Graham Taylor.'
from public.managerial_assignments ma
join public.managerial_people mp on mp.canonical_name='Martin O''Neill'
where ma.match_id=3519
on conflict (managerial_assignment_id, managerial_person_id) do update
set member_role=excluded.member_role,
    role_certainty=excluded.role_certainty,
    provenance_note=excluded.provenance_note;

-- European fixture validation batch.
update public.managerial_assignments
set assignment_certainty='confirmed',
    provenance_status='forensically_validated',
    provenance_note=case match_id
      when 3301 then 'AS Monaco v Leeds, 12 Sep 1995: Jean Tigana confirmed as Monaco manager by contemporary and match-specific records.'
      when 3305 then 'Leeds v AS Monaco, 26 Sep 1995: Jean Tigana confirmed as Monaco manager across the UEFA Cup tie.'
      when 3309 then 'Leeds v PSV, 17 Oct 1995: Dick Advocaat confirmed as PSV trainer by PSV season records and match-specific records.'
      when 3313 then 'PSV v Leeds, 31 Oct 1995: Dick Advocaat confirmed as PSV manager by match-specific records.'
      when 3448 then 'Leeds v CS Maritimo, 15 Sep 1998: Augusto Inacio confirmed as Maritimo manager by match-specific records and tenure chronology.'
      when 3451 then 'CS Maritimo v Leeds, 29 Sep 1998: Augusto Inacio confirmed as Maritimo manager by match-specific records.'
      when 3454 then 'AS Roma v Leeds, 20 Oct 1998: Zdenek Zeman confirmed as Roma manager by match-specific records.'
      when 3458 then 'Leeds v AS Roma, 3 Nov 1998: Zdenek Zeman confirmed as Roma manager by match-specific records.'
      when 3499 then 'Partizan v Leeds, 14 Sep 1999: Miodrag Jesic confirmed as Partizan coach by contemporary reporting immediately around the fixture.'
      when 3502 then 'Leeds v Partizan, 30 Sep 1999: Miodrag Jesic confirmed as Partizan coach across the UEFA Cup tie.'
      when 3513 then 'Spartak Moscow v Leeds, 2 Dec 1999: Oleg Romantsev confirmed as Spartak coach by contemporary reporting immediately before the fixture.'
      when 3515 then 'Leeds v Spartak Moscow, 9 Dec 1999: Oleg Romantsev confirmed as Spartak coach across the UEFA Cup tie.'
      else provenance_note
    end
where match_id in (3301,3305,3309,3313,3448,3451,3454,3458,3499,3502,3513,3515);
