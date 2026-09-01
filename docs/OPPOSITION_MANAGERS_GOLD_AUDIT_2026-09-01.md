# Opposition Managers Gold Audit — 2026-09-01

## Scope

This document records the finish-line forensic audit state for opposition managerial authority across all 4,856 LUFC fixtures.

## Golden rules

- Fixture-level managerial authority is the primary Gold target.
- `matches.opposition_manager_raw` is immutable provenance.
- Canonical corrections belong in canonical/relational fields, never by overwriting raw source text.
- Fixture-specific evidence outranks generic tenure dates when they conflict.
- Committees are authority entities, not fake people.
- Joint/co-manager authority must be represented by separate person links.
- Exact spell dates and caretaker/interim/permanent labels are enrichment and are not prerequisites for fixture-level Gold.
- Do not guess an exact transition date when evidence only establishes a transition window.
- User verification is mandatory before Gold lock.

## Final live relational reconciliation

Latest live Supabase reconciliation after the concentrated forensic audit and user verification:

- 4,856 matches
- 4,856 managerial assignments
- 0 missing assignments
- 0 raw-source provenance mismatches
- 0 canonical-name mismatches between `matches` and relational assignments
- 0 authority mismatches between `matches` and relational assignments
- 0 malformed joint assignments (every joint assignment has at least two linked people)
- 0 malformed individual assignments (every individual assignment has exactly one linked person)
- authority population: 4,810 individual / 15 joint/shared / 31 committee
- 130 high-risk, transition, corrected-identity or exception fixtures explicitly marked `forensically_validated`

The 130 count is an explicit forensic-review subset, not an implication that the remaining ordinary fixtures are invalid.

## User-verified representative cases

The user directly verified the following fixture-level authorities on 1 Sep 2026:

- Match 1345 — Burnley v Leeds, 23 Nov 1957: **Billy Dougall**, individual authority. Raw source spelling `Billy Dougal` remains preserved; canonical spelling is `Billy Dougall`. The earlier Dougall/Bennion uncertainty is closed for this fixture.
- Match 3293 — Leeds v Norwich City, 6 May 1995: **Gary Megson**, not stale raw-source John Deehan.
- Match 3431 — Leeds v Tottenham Hotspur, 4 Mar 1998: **Christian Gross**.
- Match 3796 — Leeds v Millwall, 7 Aug 2005: **Colin Lee**, not stale raw-source Dennis Wise.
- Match 3909 — Gillingham v Leeds, 29 Sep 2007: **Iffy Onuora + Mick Docherty**, joint caretaker managers.

## Representative committee case

- Match 240 — Manchester City v Leeds, 12 Dec 1925: **Manchester City selection committee**, with Albert Alexander represented as lead person metadata. The fixture falls within the committee-led first-team period following David Ashworth's departure. Raw source `Albert Alexander` remains preserved.

## Structurally proven joint/shared authority

The relational layer contains 15 joint/shared assignments, including:

- Birmingham City — Arthur Turner + Pat Beasley (Matches 1346, 1367)
- Coventry City — George Curtis + John Sillett (Match 2870)
- Tottenham Hotspur — Doug Livermore + Ray Clemence (Matches 3150, 3187)
- Charlton Athletic — Alan Curbishley + Steve Gritt (Matches 3177, 3179)
- Reading — Jimmy Quinn + Mick Gooding (Match 3326)
- Tottenham Hotspur — David Pleat + Chris Hughton (Match 3450)
- Middlesbrough — Terry Venables + Bryan Robson (Match 3577)
- Gillingham — Iffy Onuora + Mick Docherty (Match 3909)
- Millwall — Richard Shaw + Colin West (Match 3915)
- Leicester City — Mike Stowell + Jon Rudkin (Match 4140)
- Bristol City — John Pemberton + Wade Elliott (Match 4355)
- Rotherham United — Wayne Carlisle + Scott Brown + Dan Green (Match 4724)

## Material canonical corrections discovered during audit

Raw provenance remains unchanged in every case.

- Billy `Dougal` → canonical **Billy Dougall**, Burnley, Match 1345.
- John Deehan → **Gary Megson**, Norwich City, Match 3293.
- David Hodgson → **Jim Platt**, Darlington, Matches 3358 and 3360.
- Graham Taylor → **Martin O'Neill**, Leicester City, Match 3519.
- Dennis Wise → **Colin Lee**, Millwall, Matches 3796 and 3818.

Hidden shared-authority corrections were also made where a singular raw source concealed genuine joint control.

## Gold boundary

Fixture-level opposition managerial authority is the Gold scope. The following are explicitly Phase 2 enrichment and do not hold fixture-level Gold hostage:

- exhaustive appointment/departure dates
- complete `opposition_manager_spells`
- complete `opposition_manager_role_periods`
- exhaustive caretaker/interim/permanent role labels
- complete biographical metadata and multi-nationality enrichment

No exact dates should be manufactured for those enrichments.

## Repository state

Opposition Managers work is isolated to `lufcdata/LUFC-Data-V2`, branch `opposition-managers-gold-v1`.

The branch contains the relational schema, validation query, forensic corrections, hidden shared-authority corrections, identity corrections, and high-risk validation migrations. Live corrections that originally occurred through direct Supabase DML have been mirrored with idempotent repository migrations where they materially change canonical identity or relational authority.

## Sign-off state

All 4,856 fixtures reconcile structurally and canonically with zero current integrity mismatches. The representative user-verification set has been completed for ordinary, corrected-identity, joint-caretaker and historical edge cases; the committee case has been independently validated.

**Opposition Managers is ready for final user Gold-lock approval.**
