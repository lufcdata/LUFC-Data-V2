# Opposition Managers Gold Audit — 2026-09-01

## Scope

This document records the current forensic audit state for opposition managerial authority across all 4,856 LUFC fixtures.

## Golden rules

- Fixture-level managerial authority is the primary Gold target.
- `matches.opposition_manager_raw` is immutable provenance.
- Canonical corrections belong in canonical/relational fields, never by overwriting raw source text.
- Fixture-specific evidence outranks generic tenure dates when they conflict.
- Committees are authority entities, not fake people.
- Joint/co-manager authority must be represented by separate person links.
- Exact spell dates and caretaker/interim/permanent labels are enrichment and are not prerequisites for fixture-level Gold.
- Do not guess an exact transition date when evidence only establishes a transition window.

## Current live relational state

Migration `create_relational_opposition_manager_assignments` has been applied to live Supabase and mirrored on branch `opposition-managers-gold-v1`.

Current bootstrap reconciliation:

- 4,856 managerial assignments
- 4,856 distinct matches represented
- 875 canonical managerial people
- 17 committee identities
- 4,833 assignment-person links
- 0 assignments missing required structural representation
- authority population: 4,818 individual / 31 committee / 7 joint

The counts above describe the current structural migration state. They are **not** a claim that Opposition Managers has been signed off Gold.

## Billy Dougall / Ray Bennion — Burnley v Leeds, 23 Nov 1957

- Raw provenance remains `Billy Dougal` plus the Scotland flag.
- Canonical spelling is corrected to `Billy Dougall`.
- Evidence establishes that Dougall was hospitalised during November 1957 and Ray Bennion assumed first-team duties, but the exact handover date has not been established strongly enough to move the 23 Nov fixture.
- Gold-safe current decision: retain Billy Dougall provisionally for Match 1345; preserve Ray Bennion as an unresolved authority possibility; do not invent a transition date.

## Structurally proven non-ordinary cases now represented relationally

- Match 240: Manchester City selection committee; Albert Alexander linked as lead person.
- Matches 1346 and 1367: Arthur Turner + Pat Beasley, joint Birmingham City authority.
- Match 2870: George Curtis (born 1939) + John Sillett, joint Coventry City authority.
- Matches 3177 and 3179: Alan Curbishley + Steve Gritt, joint Charlton Athletic authority.
- Match 3326: Jimmy Quinn + Mick Gooding, joint Reading authority.
- Match 3450: David Pleat + Chris Hughton, joint Tottenham Hotspur caretaker authority.

## Short-tenure / transition audit — confirmed cases

The following assignments have survived forensic review and should not be casually rewritten:

- Les Gore — Leyton Orient, 7 Sep and 14 Sep 1960: acting/caretaker authority confirmed.
- Billy Lane — Brighton & Hove Albion, 24 Sep 1960 and 10 Feb 1961: permanent manager confirmed.
- Norman Smith — Newcastle United, 27 Jan and 28 Apr 1962: temporary/interim authority confirmed.
- Johnny Hart — Manchester City, 31 Mar 1973: assignment consistent with Manchester City managerial chronology.
- Ronnie/Ron Fenton — Notts County, 3 Jan 1976: manager assignment confirmed by contemporary-season match evidence.
- Colin Murphy — Derby County, 12 Feb 1977: Derby's own history confirms he first took temporary control and was appointed permanently in February 1977.
- Brian Green — Rochdale, 31 Aug 1977: managerial tenure runs 1 Jun 1976 to 1 Sep 1977, so the fixture falls within his authority.
- George Eastham — Stoke City, 12 Apr 1977: manager from March 1977; assignment retained.
- Bobby Roberts — Colchester United, 26 Oct 1977: Colchester manager 1975–82; assignment retained.
- John Wile — West Bromwich Albion, 31 Dec 1977: caretaker authority confirmed.
- Brian Garvey — Wolves, 18 Nov 1978: temporary/caretaker authority confirmed after Sammy Chung's 8 Nov departure and before John Barnwell from 20 Nov.
- David Pleat — Luton Town, 13 Dec 1978: appointment in 1978 confirmed; assignment retained.
- Billy Horner — Hartlepool United, 18 Jan 1979: club history records appointment in Oct 1976 and a seven-year stint; assignment retained.
- Alan Mullery — Brighton & Hove Albion, 13 Oct 1979: Brighton club history confirms he took charge in 1976 and led promotion in 1978/79; assignment retained.
- Terry Venables — Crystal Palace, 1 Dec 1979: retained pending no contrary fixture evidence.
- John Barnwell — Wolves, 15 Dec 1979: retained; contemporary Wolves history places him in charge during Dec 1979.
- Alan Durban — Stoke City, 21 Dec 1979: retained; documented Stoke tenure began Feb 1978 and continued to 1981.

## Remaining work before Gold sign-off

1. Continue chronological rare-manager and transition-case audit beyond the completed 1960s/1970s pass.
2. Detect hidden joint/co-manager/caretaker structures currently represented as ordinary individuals.
3. Populate `opposition_manager_spells` and `opposition_manager_role_periods` only where defensible evidence exists; do not manufacture exact dates.
4. Add multi-nationality person records where supported.
5. Reconcile all 4,856 relational assignments against source provenance and canonical match columns.
6. Run final structural, provenance, duplicate, orphan, and fixture-count validation.
7. Only then propose Opposition Managers Gold sign-off for user verification.

## Repository safety

All Opposition Managers work is isolated to `lufcdata/LUFC-Data-V2` and branch `opposition-managers-gold-v1`. No other football repository is in scope.
