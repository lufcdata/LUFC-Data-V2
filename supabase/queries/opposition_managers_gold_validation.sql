-- Opposition Managers Gold validation pack

-- 1. Exactly one assignment per historical fixture.
select
  (select count(*) from public.matches) as match_count,
  count(*) as assignment_count,
  count(distinct match_id) as distinct_assignment_matches
from public.managerial_assignments;

-- 2. Structural representation: every non-committee assignment has people;
-- every committee assignment has a committee entity.
select count(*) as assignments_without_required_structure
from public.managerial_assignments ma
where (ma.authority_type = 'committee' and ma.managerial_committee_id is null)
   or (ma.authority_type <> 'committee' and not exists (
        select 1
        from public.managerial_assignment_people map
        where map.managerial_assignment_id = ma.managerial_assignment_id
   ));

-- 3. Joint assignments must have at least two linked people.
select ma.match_id, count(map.managerial_person_id) as linked_people
from public.managerial_assignments ma
left join public.managerial_assignment_people map
  on map.managerial_assignment_id = ma.managerial_assignment_id
where ma.authority_type = 'joint'
group by ma.match_id
having count(map.managerial_person_id) < 2
order by ma.match_id;

-- 4. Provenance must reconcile exactly with matches.opposition_manager_raw.
select ma.match_id, ma.source_raw, m.opposition_manager_raw
from public.managerial_assignments ma
join public.matches m using (match_id)
where ma.source_raw is distinct from m.opposition_manager_raw
order by ma.match_id;

-- 5. Authority classification must reconcile with canonical match classification.
select ma.match_id, ma.authority_type, m.opposition_manager_authority_type
from public.managerial_assignments ma
join public.matches m using (match_id)
where ma.authority_type is distinct from m.opposition_manager_authority_type
order by ma.match_id;

-- 6. Orphan assignment people.
select map.*
from public.managerial_assignment_people map
left join public.managerial_assignments ma
  on ma.managerial_assignment_id = map.managerial_assignment_id
left join public.managerial_people mp
  on mp.managerial_person_id = map.managerial_person_id
where ma.managerial_assignment_id is null
   or mp.managerial_person_id is null;

-- 7. Current authority distribution.
select authority_type, count(*)
from public.managerial_assignments
group by authority_type
order by authority_type;

-- 8. Audit queue: provisional assignments, oldest first.
select m.match_id, m.match_date, c.display_name as opponent,
       ma.authority_type, ma.canonical_display, ma.audit_status, ma.notes
from public.managerial_assignments ma
join public.matches m on m.match_id = ma.match_id
join public.clubs c on c.club_id = m.opponent_id
where ma.audit_status <> 'gold'
order by m.match_date, m.match_id;
