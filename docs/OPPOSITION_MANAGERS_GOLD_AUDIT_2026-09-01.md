# Opposition Managers Gold Audit — 2026-09-01

## GOLD STATUS

**OPPOSITION MANAGERS — GOLD LOCKED**

User Gold-lock approval received on **1 September 2026** after final live reconciliation and representative fixture verification.

This Gold lock protects fixture-level opposition managerial authority across all 4,856 LUFC fixtures. Future work must not silently rewrite these definitions or assignments. Any proposed correction must preserve raw provenance, be evidence-led, be separately audited, and receive explicit approval before altering the Gold layer.

## Scope

Fixture-level managerial authority is the Gold target. Raw source, canonical identity and relational authority are deliberately separated.

## Golden rules

- `matches.opposition_manager_raw` is immutable provenance.
- Canonical corrections belong in canonical/relational fields, never by overwriting raw source text.
- Fixture-specific evidence outranks generic tenure dates when they conflict.
- Committees are authority entities, not fake people.
- Joint/co-manager authority must be represented by separate person links.
- Exact spell dates and caretaker/interim/permanent labels are enrichment and are not prerequisites for fixture-level Gold.
- Do not guess an exact transition date when evidence only establishes a transition window.
- Gold assignments must not be casually rewritten or simplified.
- User verification is required before any future material change to this Gold layer.

## Final live relational reconciliation at Gold lock

- 4,856 matches
- 4,856 managerial assignments
- 4,856 distinct matches represented
- 0 missing assignments
- 0 raw-source provenance mismatches
- 0 canonical-name mismatches between `matches` and relational assignments
- 0 authority mismatches between `matches` and relational assignments
- 0 malformed joint assignments
- 0 malformed individual assignments
- authority population: **4,810 individual / 15 joint/shared / 31 committee**
- **130** high-risk, transition, corrected-identity or exception fixtures explicitly marked `forensically_validated`

The 130 count is an explicit forensic-review subset, not an implication that the remaining ordinary fixtures are invalid.

## User-verified representative cases

Directly verified by the user on 1 Sep 2026:

- Match 1345 — Burnley v Leeds, 23 Nov 1957: **Billy Dougall**, individual. Raw `Billy Dougal` preserved; earlier Dougall/Bennion uncertainty closed for this fixture.
- Match 3293 — Leeds v Norwich City, 6 May 1995: **Gary Megson**, not stale raw-source John Deehan.
- Match 3431 — Leeds v Tottenham Hotspur, 4 Mar 1998: **Christian Gross**.
- Match 3796 — Leeds v Millwall, 7 Aug 2005: **Colin Lee**, not stale raw-source Dennis Wise.
- Match 3909 — Gillingham v Leeds, 29 Sep 2007: **Iffy Onuora + Mick Docherty**, joint caretaker managers.

## Representative committee case

- Match 240 — Manchester City v Leeds, 12 Dec 1925: **Manchester City selection committee**, with Albert Alexander represented as lead-person metadata. Raw source `Albert Alexander` remains preserved.

## Structurally proven joint/shared authority

The Gold layer contains 15 joint/shared assignments, including:

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

## Gold boundary / Phase 2

The following are later enrichment and **must not reopen fixture-level Gold by default**:

- exhaustive appointment/departure dates
- complete `opposition_manager_spells`
- complete `opposition_manager_role_periods`
- exhaustive caretaker/interim/permanent role labels
- complete biographical metadata and multi-nationality enrichment

No exact dates should be manufactured for those enrichments.

## Repository state at sign-off

Repository: `lufcdata/LUFC-Data-V2`

Gold working branch: `opposition-managers-gold-v1`

At the final pre-lock comparison the branch was ahead of `main` and not behind it. It contains the relational schema, validation query, forensic corrections, hidden shared-authority corrections, identity corrections and high-risk validation migrations. Material live DML corrections are mirrored by idempotent repository migrations using stable canonical joins rather than generated-ID assumptions.

## Final sign-off

Final engineering reconciliation: **PASS**.

Representative user verification: **PASS**.

Explicit user Gold-lock approval: **RECEIVED — 1 September 2026**.

# OPPOSITION MANAGERS — GOLD LOCKED
