# LUFC DATA V2 — STAT PACK GOLDEN MOMENT HANDOVER

**Status:** 6 September 2026

**Repository:** `lufcdata/LUFC-Data-V2`

**Working branch:** `ui-bolt-opponents-v1`

**Golden Moment purpose:** preserve the current Stat Pack research architecture, scope rules, physical-stadium identity, quality gate, Yorkshire Derby definition and all associated safeguards before further development.

---

## MANDATORY FIRST ACTION FOR THE NEXT CHAT

Before changing anything:

1. Inspect the current GitHub `ui-bolt-opponents-v1` HEAD.
2. Read this handover in full.
3. Inspect the current implementations of:
   - `frontend/src/StatPack.tsx`
   - `frontend/src/statPackFixtureResearch.ts`
   - `frontend/src/statPackResearchQuality.ts`
   - `frontend/src/statPackFixtureScope.ts`
   - `frontend/src/stadiumIdentity.ts`
   - `frontend/src/statPackYorkshireDerby.ts`
4. Verify the latest GitHub Actions run for the current HEAD.
5. Treat the current repository as the latest code source of truth. This document is authoritative project context, but GitHub HEAD always wins if something has moved.

Do not make a code change before completing those checks.

---

# THE GOLDEN RULE

**ONE DEFINITION → ONE AUTHORITATIVE POPULATION → EVERY RELEVANT SURFACE.**

The Stat Pack must not independently recalculate the same concept in multiple places with subtly different scopes.

A stat is only as good as its population definition.

For opponent / fixture research, scope contamination is a critical bug.

Examples of invalid scope contamination:

- a home fixture triggering an away-only opponent story;
- Premier League research silently absorbing Championship or Division One matches;
- stadium sponsor/name changes splitting one physical venue into separate histories;
- all-venue H2H streaks competing against an exact competition + H/A research family;
- two separate modules calculating the same football concept differently.

---

# STAT PACK PRODUCT VISION

The Stat Pack is intended to behave like an Opta-quality pre-match research machine.

It should not simply output lots of statistics. It should surface a small number of genuinely useful, broadcast-quality historical findings.

The three conceptual layers are:

1. **What Leeds bring into the match**
2. **What the selected opponent / fixture context specifically triggers**
3. **What could happen in the upcoming match**

The preferred causality chain is:

**Trigger → Achievement → Historical Significance**

A streak on its own is usually not Grade A. The historical comparison is what earns the stat its place.

Preferred Grade A hierarchy:

1. Record
2. First
3. Since
4. Longest / joint-longest
5. Historical ranking
6. At-stage comparison
7. Rare exception
8. Before/after transformation
9. Cross-era leaderboard
10. Ordinary trend

Target output is roughly 10–20 exceptional facts, not volume for volume's sake.

---

# CURRENT STAT PACK ARCHITECTURE

## Main surface

`frontend/src/StatPack.tsx`

Read-only source tables currently include:

- `match_centre_summary`
- `goals`
- `players`
- `player_matches`

The main page handles:

- fixture selector UI
- loading the archive
- player / manager / team research that remains local to the page
- ranking / final top-24 presentation
- evidence toggle
- calling the fixture-aware research engine when authoritative fixture context exists

## Fixture-aware research engine

`frontend/src/statPackFixtureResearch.ts`

This owns exact upcoming-fixture historical research and now returns findings through the central quality gate.

The engine requires authoritative context:

- opponent
- competition
- H/A venue
- season
- optional stadium
- optional manager

## Research quality gate

`frontend/src/statPackResearchQuality.ts`

Current safe policy:

- sort by priority
- exact normalized text dedupe
- one strongest Grade A item per authoritative family
- Grade B contextual findings may coexist
- **no speculative cross-family semantic suppression**

Important lesson: an earlier attempt to suppress one family merely because another related family existed was too aggressive. Do not infer football-semantic redundancy from family names or text alone.

Cross-family dedupe must only be done where the research engine knows the exact underlying populations / runs / comparators.

## Exact fixture scope helper

`frontend/src/statPackFixtureScope.ts`

Canonical exact opponent fixture population:

**opponent + exact competition + exact H/A**

This intentionally does not treat Premier League, Championship, Division One, Division Two or League One as interchangeable populations.

Use this when a finding claims to be about the selected fixture context.

## Physical stadium identity

`frontend/src/stadiumIdentity.ts`

Core invariant:

> STADIUM STATISTICS MUST USE PHYSICAL VENUE IDENTITY, NEVER THE RAW STADIUM NAME.

Historical raw `stadium` labels remain preserved for display / evidence.

The analytical layer canonicalises verified same-ground naming changes.

No fuzzy matching.

No auto-merge.

No unverified aliases.

Verified same-physical-venue examples include:

- City of Manchester Stadium → Etihad Stadium
- Britannia Stadium → Bet365 Stadium
- JJB Stadium → DW Stadium
- Reebok Stadium / Macron Stadium → University of Bolton Stadium
- Ricoh Arena → Coventry Building Society Arena
- KC Stadium / KCOM Stadium → MKM Stadium
- Liberty Stadium → Swansea.com Stadium
- McAlpine Stadium → John Smith's Stadium
- Brentford Community Stadium → Gtech Community Stadium
- Walkers Stadium → King Power Stadium
- Dean Court → Vitality Stadium

Replacement grounds must remain distinct, for example:

- Highbury ≠ Emirates
- Maine Road ≠ Etihad
- White Hart Lane ≠ Tottenham Hotspur Stadium
- Goodison Park ≠ Hill Dickinson Stadium
- Filbert Street ≠ King Power Stadium
- The Dell ≠ St Mary's
- Highfield Road ≠ Coventry Building Society Arena
- Leeds Road ≠ John Smith's Stadium
- Boothferry Park ≠ MKM Stadium
- Vetch Field ≠ Swansea.com Stadium
- Griffin Park ≠ Gtech Community Stadium

---

# YORKSHIRE DERBY DEFINITION — NOW LOCKED

The user has explicitly defined the Leeds United Yorkshire Derby population as matches against exactly these clubs:

- Barnsley
- Bradford City
- Doncaster Rovers
- Huddersfield Town
- Hull City
- Rotherham United
- Rotherham County
- Sheffield United
- Sheffield Wednesday

This is the authoritative list.

Do not add other Yorkshire clubs without explicit approval.

Do not remove any of these clubs without explicit approval.

Do not infer derby membership geographically.

The canonical code lives in:

`frontend/src/statPackYorkshireDerby.ts`

Current functions include:

- `isYorkshireDerbyOpponent(...)`
- `yorkshireDerbyMatches(...)`
- `yorkshireDerbyRecord(...)`

The canonical record calculation returns:

- matches
- wins
- draws
- defeats
- goals for
- goals against

The Stat Pack currently surfaces Yorkshire Derby context only when the upcoming opponent is one of the signed-off derby clubs.

Current editorial treatment is Grade B context, not a Grade A historical claim by default.

Current wording reports Leeds' recorded competitive W-D-L derby record plus goals scored / conceded.

Important architectural note: the central `yorkshireDerbyRecord(...)` helper was added after the first Stat Pack wiring. Before any future refactor, inspect whether `statPackFixtureResearch.ts` is consuming that helper directly or still locally deriving W/D/L from the already-canonical derby population. If local calculation remains, the safest cleanup is to switch the research engine to the central helper **without changing population or wording semantics**. Do not combine that cleanup with any new derby definition.

---

# CURRENT FIXTURE RESEARCH FAMILIES

The fixture-aware engine currently contains these research families:

1. Manager consecutive home/away wins
2. Opening home/away season wins exact-stage history
3. Stadium winning sequence using physical stadium identity
4. Opponent + fixture venue winning sequence
5. Opponent + fixture venue unbeaten sequence
6. Opponent + fixture venue losing-sequence risk
7. Opponent + fixture venue scoring sequence
8. Opponent + fixture venue scoring drought breaker
9. Opponent + fixture venue two-goal scoring significance
10. Opponent + fixture venue multi-goal win significance (2+ margin)
11. Opponent + fixture venue emphatic win significance (3+ margin)
12. Opponent + fixture venue win-to-nil significance
13. Opponent + fixture venue clean-sheet sequence
14. First-goal recent protection / recovery Grade B context
15. First-goal opponent-specific outcome Grade B context
16. First-goal exact-stage season historical significance
17. First-goal opponent-conditioned historical sequence
18. Clean-sheet exact-stage season history
19. Opponent clean-sheet sequence across all venues
20. Clean-sheet winning formula Grade B context
21. Yorkshire Derby competitive record Grade B context

---

# IMPORTANT DEDUPE / QA LEARNINGS

## Winning vs unbeaten sequences

Do not display a weaker unbeaten sequence when it is literally identical to the current winning run.

But retain unbeaten if it genuinely extends beyond the winning run.

Examples:

- W-W-W → winning run only
- D-W-W-W → unbeaten may remain because it is broader
- W-D-W → unbeaten is distinct

## 2+ margin vs 3+ margin wins

The emphatic 3+ family should not repeat the same historical comparator already carried by the broader 2+ multi-goal-win family.

If the latest relevant 2+ and 3+ comparators are the same match, suppress the redundant 3+ since-story.

If the 3+ story has a genuinely different older comparator, it can remain.

## Clean-sheet overlap

Potential overlap still requiring careful fixture QA:

- exact-venue opponent clean-sheet sequence
- all-venue opponent clean-sheet sequence
- win-to-nil significance

Do not blanket-suppress any of these by family name.

A safe future rule should compare the actual trailing match populations / match IDs. If the all-venue clean-sheet sequence is exactly the same underlying sequence as the more precise venue-conditioned sequence, prefer the precise story. If it genuinely extends across the other venue, it may be editorially distinct.

## Two-goal scoring vs multi-goal win

These are different questions:

- scoring two or more = attacking output regardless of result
- winning by two or more = result + margin

Do not suppress blindly.

## Legacy opponent streaks

Broad all-venue / all-competition legacy H2H streaks are fallback research only once exact fixture context exists.

The exact fixture-aware research engine should own opponent sequences when competition + H/A are known.

## Legacy away win opportunity

This was previously scope-contaminated because it could produce an away-opponent story regardless of the selected upcoming venue.

It has been corrected to use the selected opponent + selected competition + Away context.

A home fixture should never trigger an away-only opportunity.

---

# FIRST-GOAL SEMANTICS

Verified meanings in the archive:

- `Scored` = Leeds scored first
- `Conceded` = Leeds conceded first
- `None` = no first goal, normally 0-0
- `TBC` = unresolved / incomplete record

Do not reinterpret these values.

---

# CLEAN-SHEET INVARIANT

Canonical clean sheet condition:

`opponent_score === 0`

This includes 0-0 draws.

For wins to nil specifically use:

`result === 'Won' && opponent_score === 0`

Do not use the two definitions interchangeably.

---

# PROTECTED / DO-NOT-BREAK AREAS

## Match Log

`/test/a1` Match Log is protected / signed off.

Do not casually alter:

- Match Log internals
- width
- W/D/L badges
- goal markers
- selectors

Production Player Page should remain untouched unless explicitly requested.

## Supabase data

Stat Pack work is read-only.

Do not perform Supabase INSERT / UPDATE / DELETE / migration writes for Stat Pack development unless the user explicitly authorises a separate data task.

## Brighton match intake

The prior Brighton intake dry-run rule was read-only until full-time unless explicitly changed.

Do not conflate that ingestion workflow with Stat Pack research work.

---

# GITHUB WRITE DISCIPLINE — MANDATORY

Before every write:

1. Fetch current branch HEAD.
2. Fetch the current target file and blob SHA.
3. Fetch the complete current blob for any large replacement file.
4. Never write using a stale SHA.
5. Make one semantic change at a time.

After every write:

1. Capture commit SHA.
2. Find the exact GitHub Actions run for that exact `head_sha`.
3. Inspect the jobs.
4. Only call the commit build-safe when:
   - `frontend-build` completed successfully;
   - `Run npm run build` succeeded;
   - `Run pytest -q` succeeded.

The workflow can still show overall failure because of the known separate `Audit player icon mapping` failure.

Do not treat that known icon-audit failure as a Stat Pack regression.

Do not start the next write while the previous semantic change is still awaiting CI verification.

---

# TYPECHECK LESSON

An attempted build hardening changed `npm run build` to invoke a TypeScript config called `tsconfig.app.json`.

That file did not exist in this frontend, so CI failed before Vite could build.

The build script was restored immediately.

Lesson:

Do not invent or assume frontend TypeScript config filenames. Inspect the actual frontend configuration first.

The current working build command remains the repository's existing Vite build flow.

---

# RECENT IMPORTANT COMMITS

The following sequence captures the main Stat Pack / QA progression leading into this Golden Moment:

- `3d54e5158b7a3adea4216c47d6b92f1be38fea2d` — Apply Stat Pack fixture research quality gate
- `8883bec4afdf8f7a3077490f93e15fa33002354c` — Make Stat Pack quality gate conservative
- `b48b00026b7ce9f22f43814d6b5d740891e2a611` — Add Stat Pack research quality policy
- `a697b5e305a385893d24bac464338f33d40e7f18` — Add opponent venue losing-sequence risk
- `8dca7c7f0f6c30b06987e5f726b40f81245c526b` — Suppress redundant emphatic-win research
- `1caa457196e4c59881c35560a0daba039aa23bf1` — Deduplicate opponent venue winning and unbeaten runs
- `c92cfa695363207dcfbf64104bac001f51a67022` — Add opponent venue two-goal scoring research
- `48b7842c56a0ea286030112fa3bc3649f0e18413` — Add opponent venue win-to-nil research
- `c6eb98977a0ce5ba8e6b4ee4c4d62ab28bce1eb7` — Add opponent venue multi-goal win research
- `d4e8ddf54758d242857841453ee3389ef88b57cb` — Add canonical exact fixture scope helper
- `ea3a2b3b4335676c56d839e94c4f27635355b435` — Scope legacy away opportunities to selected fixture
- `ce7ca17dd502348d6fc2bc6e64e43d0c4fcf5512` — Suppress legacy opponent streaks with exact fixture context
- `bbb52be4fedff35e60b2171db945bb8c6c72429d` — Add canonical Yorkshire derby scope
- `5e2b7b6c8f7527f119efd7ed523baff27c2847a7` — Add Yorkshire derby record to Stat Pack research
- `47c23b4defb858845fad06a7dfc42a90a9e06d44` — Centralise Yorkshire derby record calculation

The exact current HEAD must still be re-checked by the inheriting chat before writing.

---

# GOLDEN-MOMENT STATE AT HANDOVER CREATION

Immediately before this handover document was written, the inspected working-branch HEAD was:

`47c23b4defb858845fad06a7dfc42a90a9e06d44`

Commit message:

`Centralise Yorkshire derby record calculation`

Its exact CI run was:

`33999309993`

Verified result:

- `frontend-build`: success
- `Run npm run build`: success
- `Run pytest -q`: success
- workflow overall failure only because of the known `Audit player icon mapping` failure

Therefore that code state is considered build-safe under the established project rule.

This handover commit comes after that code state and is documentation-only. Verify its CI before treating the final documentation commit as the immutable Golden Moment pointer.

---

# RECOMMENDED NEXT TASKS

The project has reached the point where **real-fixture QA and ranking calibration are more valuable than adding lots of new research families**.

Highest-value next work:

1. Verify Yorkshire Derby output on several real derby opponents and confirm the archive population contains only the signed-off nine clubs.
2. Ensure `statPackFixtureResearch.ts` directly consumes the canonical `yorkshireDerbyRecord(...)` helper if it does not already do so; this should be a semantics-preserving cleanup only.
3. QA clean-sheet cross-family overlap using actual trailing match IDs.
4. Audit remaining legacy Stat Pack blocks for fixture-scope contamination before adding new families.
5. Calibrate priorities using real upcoming fixtures and suppress only demonstrably redundant stories.
6. Keep Grade B context useful but subordinate to Grade A record / first / since findings.

Avoid adding a generic record-margin family just for more output. Existing 2+ and 3+ margin families already cover the meaningful territory.

---

# WORKING PRINCIPLE FOR THE NEXT CHAT

When the user says **"keep going"**, they expect implementation, not discussion.

Proceed with:

**inspect → one safe change → exact CI verification → next change**

Do not claim something is implemented unless it is actually committed.

Do not claim something is build-safe until the exact run for that exact commit has been inspected.

Preserve the Golden Moment before taking further architectural risks.
