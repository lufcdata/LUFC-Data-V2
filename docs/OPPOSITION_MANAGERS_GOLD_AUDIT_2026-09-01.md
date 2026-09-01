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

Current reconciliation after the Livermore/Clemence joint-authority correction:

- 4,856 managerial assignments
- 4,856 distinct matches represented
- 0 assignments missing required structural representation
- 0 joint assignments with fewer than two people
- 0 raw provenance mismatches
- 0 authority mismatches between matches and relational assignments
- authority population: 4,816 individual / 31 committee / 9 joint

These counts describe the current structural state. They are **not** a claim that Opposition Managers has been signed off Gold.

## Billy Dougall / Ray Bennion — Burnley v Leeds, 23 Nov 1957

- Raw provenance remains `Billy Dougal` plus the Scotland flag.
- Canonical spelling is corrected to `Billy Dougall`.
- Evidence establishes that Dougall was hospitalised during November 1957 and Ray Bennion assumed first-team duties, but the exact handover date has not been established strongly enough to move the 23 Nov fixture.
- Gold-safe current decision: retain Billy Dougall provisionally for Match 1345; preserve Ray Bennion as an unresolved authority possibility; do not invent a transition date.

## Structurally proven non-ordinary cases now represented relationally

- Match 240: Manchester City selection committee; Albert Alexander linked as lead person.
- Matches 1346 and 1367: Arthur Turner + Pat Beasley, joint Birmingham City authority.
- Match 2870: George Curtis (born 1939) + John Sillett, joint Coventry City authority.
- Matches 3150 and 3187: Doug Livermore + Ray Clemence, joint Tottenham Hotspur authority during 1992-93.
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
- Brian Green — Rochdale, 31 Aug 1977: managerial tenure runs to 1 Sep 1977, so the fixture falls within his authority.
- George Eastham — Stoke City, 12 Apr 1977: manager from March 1977; assignment retained.
- Bobby Roberts — Colchester United, 26 Oct 1977: Colchester manager 1975–82; assignment retained.
- John Wile — West Bromwich Albion, 31 Dec 1977: caretaker authority confirmed.
- Brian Garvey — Wolves, 18 Nov 1978: temporary/caretaker authority confirmed after Sammy Chung's departure and before John Barnwell.
- David Pleat — Luton Town, 13 Dec 1978: appointment in 1978 confirmed; assignment retained.
- Billy Horner — Hartlepool United, 18 Jan 1979: club history supports his long first spell; assignment retained.
- Alan Mullery — Brighton & Hove Albion, 13 Oct 1979: club history confirms he was in charge; assignment retained.
- Ernie Walley — Crystal Palace, 25 Oct 1980: caretaker authority confirmed.
- Ken Craggs — Charlton Athletic, 6 Nov 1982: fixture falls before his 22 Nov 1982 departure; assignment confirmed.
- Frank Casper — Burnley, 9 Apr 1983: caretaker manager Jan–Jun 1983; fixture assignment confirmed.
- Jimmy Goodfellow — Cardiff City, 12 Sep 1984: sole manager by this fixture. Earlier joint-caretaker period with Jimmy Mullen ended in April 1984, so this is not a hidden joint case.
- Peter Grotier — Grimsby Town, 19 Oct 1985: Grimsby club history identifies him as caretaker manager in 1985.
- Steve Smith — Huddersfield Town, 3 Jan 1987: caretaker authority confirmed; became permanent manager on 13 Jan 1987.
- Steve Smith — Huddersfield Town, 15 Sep 1987: permanent-manager authority confirmed.
- Malcolm Crosby — Oxford United, 3 Jan 1998: temporary/caretaker authority confirmed after Denis Smith's departure.

## Newly discovered hidden joint authority

### Tottenham Hotspur 1992-93 — Doug Livermore + Ray Clemence

The legacy source stored only `Doug Livermore` for both Leeds fixtures. Tottenham historical material and independent contemporary-era records support a shared first-team/co-manager arrangement between Doug Livermore and Ray Clemence from May 1992 to June 1993.

Affected Leeds fixtures:

- Match 3150 — 25 Aug 1992
- Match 3187 — 20 Feb 1993

Gold correction applied live:

- Raw `Doug Livermore` provenance preserved.
- Authority changed from individual to joint.
- Doug Livermore remains linked.
- Ray Clemence added as a second stable person identity and linked to both assignments.
- Both person links carry joint-role metadata.

## Remaining work before Gold sign-off

1. Continue chronological rare-manager and transition-case audit through the remaining 1990s, 2000s and European opposition population.
2. Continue systematic hidden joint/co-manager/caretaker detection.
3. Populate `opposition_manager_spells` and `opposition_manager_role_periods` only where defensible evidence exists; do not manufacture exact dates.
4. Add multi-nationality person records where supported.
5. Reconcile all 4,856 relational assignments against source provenance and canonical match columns after every correction batch.
6. Run final structural, provenance, duplicate, orphan, and fixture-count validation.
7. Only then propose Opposition Managers Gold sign-off for user verification.

## Repository safety

All Opposition Managers work is isolated to `lufcdata/LUFC-Data-V2` and branch `opposition-managers-gold-v1`. No other football repository is in scope.
