# LUFC DATA V2 — MASTER HANDOVER — 7 SEPTEMBER 2026

## GOLDEN MOMENT: SAFE POST-MATCH INGESTION + APPEARANCE POPULATION

This document is the authoritative handover for the next ChatGPT chat. It records the state reached after the 5 September 2026 Brighton & Hove Albion v Leeds United ingestion, the discovery and repair of the unused-substitute appearance bug, and the hardening of the future SofaScore ingestion pipeline.

## START HERE

Repository: `lufcdata/LUFC-Data-V2`
Working branch: `ui-bolt-opponents-v1`
Golden snapshot branch created from the handover commit: `golden-ingestion-2026-09-07`
Production Supabase project ref: `nztiaxnrwojraiwipwjj`
Permanent database Golden branch: `golden-database-2026-09-06` — NEVER DELETE.
Stat Pack Golden branch: `golden-statpack-2026-09-06`.

Before changing anything, inspect current GitHub HEAD and read this document. GitHub HEAD is always code source of truth. Also retain the Golden Rules from the Sep 2, Sep 3, Sep 5 and Sep 6 handovers.

Central architecture rule:

> **ONE DEFINITION → ONE AUTHORITATIVE POPULATION → EVERY RELEVANT SURFACE.**

Ingestion quality rule:

> **COMPLETE → CORRECT → CONSISTENT → REVERSIBLE → ONLY THEN CANONICAL.**

Fail-closed rule:

> **IMPORT BLOCKED — INCOMPLETE OR UNRESOLVED.**

## THE GOLDEN APPEARANCE RULE

The Brighton incident established a permanent non-negotiable rule:

> **NAMED ON THE BENCH ≠ APPEARANCE.**
>
> **Appearance population = starting XI + substitutes PROVEN to have entered the pitch.**

For a normal match:
- exactly 11 starters;
- every substitute appearance must have a proven `player_on` relationship in `match_substitutions`;
- the set of substitute player IDs in `player_matches` must equal the set of `match_substitutions.player_on_id` values;
- named unused substitutes remain source/bench evidence only and MUST NOT enter `player_matches`;
- unused substitutes therefore receive no appearance, substitute appearance, debut, manager appearance or other statistic derived from appearances;
- duplicate player-on identities block ingestion;
- a player-on identity not present on the named bench blocks source validation;
- missing/extra substitute appearances block canonical diff/promotion;
- apply the same source-population validation independently to Leeds and the opponent. Opposition players must never be forced into the Leeds `players` namespace.

This rule is structural, not a Brighton-specific correction.

## BRIGHTON INCIDENT AND REPAIR

Fixture: 5 September 2026 — Brighton & Hove Albion 1–1 Leeds United, Premier League.
Canonical match ID: 4857.
SofaScore event ID: 16363258.

The original production import incorrectly created 20 `player_matches`: 11 starters + all nine named substitutes. Leeds actually used four substitutes.

Correct used substitutes:
- Jaka Bijol (888)
- Brenden Aaronson (853)
- Harry Wilson (898)
- Lukas Nmecha (887)

Unused substitutes that were incorrectly counted and then removed:
- Michael Zetterer (902), erroneous player_match 58544
- Daniel James (844), erroneous player_match 58545
- Sean Longstaff (891), erroneous player_match 58546
- Jean-Matteo Bahoya (904), erroneous player_match 58547
- Melvin Bard (903), erroneous player_match 58548

Production was repaired with an assertion-heavy, fail-closed transaction. Post-repair production checks proved:
- player_matches = 15;
- starters = 11;
- substitute appearances = 4;
- proven players-on = 4;
- substitute appearances without proven player-on = 0;
- proven players-on missing an appearance = 0;
- known unused-bench contamination = 0.

Downstream checks also showed Match Centre player surfaces derive from corrected `player_matches`: 15 Match Centre players, 15 player-fact rows and four substitutions. The five unused players contribute zero Brighton appearances.

## BRIGHTON VERIFIED FACTS

- FT Brighton 1–1 Leeds; HT Brighton 0–1 Leeds.
- Jayden Bogle 15', assisted Ao Tanaka.
- Luka Vušković 71', assisted Maxim De Cuyper.
- Leeds XI: James Trafford; Jayden Bogle; Gabriel Gudmundsson; Ethan Ampadu; Tarik Muharemović; Dominic Calvert-Lewin; Anton Stach; Noah Okafor; Ao Tanaka; James Justin; Nico Elvedi.
- Leeds used subs: Bijol 61, Aaronson 62, Wilson 73, Nmecha 73.
- Leeds unused bench: Zetterer, Daniel James, Longstaff, Bahoya, Bard.
- Leeds captain Ethan Ampadu.
- Referee Stuart Attwell.
- Attendance 31,661, manually verified from BBC because SofaScore attendance was null.
- Canonical stadium convention: `Amex Stadium, Brighton`.
- Leeds formation: 3-5-2.
- League position after match: 9th, 5 points.
- Bogle goal final authoritative taxonomy: **Corner (3rd Phase) / 6 Yard / Right Foot**. Never revert to 2nd Phase.

## INGESTION PIPELINE

Target architecture:

**SofaScore → immutable raw capture → staging → identity reconciliation → validation → proposed canonical diff → verified pre-import backup → controlled promotion → canonical LUFC database → app**

The scraper must NEVER write directly into canonical LUFC tables.

Phase 1 should remain conservative: automatic collection and validation, human approval for production promotion. Only consider fully automatic promotion after a substantial clean run of verified matches.

### Provider identity rule

> **EXTERNAL PROVIDER IDENTIFIERS MUST NEVER OCCUPY LUFC CANONICAL ID FIELDS. ALL PROVIDER IDS PASS THROUGH AN EXPLICIT, PROVIDER-NAMESPACED IDENTITY-MAPPING LAYER.**

SofaScore Leeds team ID = 34. Brighton = 30.

### Promotion gate

Promotion must fail closed unless fixture identity, player/manager identity, XI, appearance population, substitutions, score, goals and other required facts reconcile. Required source validation now explicitly includes `appearance_population`.

## IMPLEMENTED APPEARANCE SAFEGUARDS

### `scripts/sofascore_appearance_population.py`
Defines and validates starters, used substitutes, unused bench and appearance population. Exactly 11 starters. Used players-on must be named bench players. Duplicate player-on IDs block. Same contract can be run for Leeds and opponent.

### `scripts/sofascore_source_derived_dry_run.py`
Extracts substitution `playerIn.id` evidence by side, validates both appearance populations and serialises starter/used/unused/appearance IDs and counts into the source bundle.

### `scripts/sofascore_source_canonical_diff.py`
Filters the Leeds canonical appearance proposal to starters plus provider IDs in `used_substitute_ids`. Unused bench is excluded.

### `scripts/sofascore_canonical_diff.py`
The deeper structural fix. It no longer assumes a 20-player named squad equals 20 appearances. It requires exactly 11 starters and requires substitute appearance provider IDs to equal the distinct proven substitution player-on population. Mismatch blocks the diff.

### Promotion
`sofascore_dry_run_contract.py` and `sofascore_promotion_gate.py` require `appearance_population` validation.

### Brighton regression
`tests/test_sofascore_canonical_diff.py` now permanently encodes the Brighton shape:
- 20 named squad members as source context;
- 11 starters;
- four used substitutes;
- five unused substitutes;
- canonical appearance population exactly 15;
- trying to send all 20 into `player_matches` must BLOCK;
- missing a used substitute must BLOCK;
- duplicate player-on must BLOCK;
- Bogle goal taxonomy regression is locked to Corner (3rd Phase) / 6 Yard / Right Foot.

Never weaken these tests to make an import pass.

## IMPORTANT COMMITS IN THIS GOLDEN SEQUENCE

- `e938f63232b5ca5b87f97ccc55cddfe0e32b62f3` — Block unused bench players from appearance populations
- `9cd4c37daaa0ba1699284d97d54942118f3b5723` — Test Leeds and opponent appearance population gate
- `61a5f77834241432a99d82ef43e78bda991cfcf0` — Validate source appearance populations
- `36cb8fcdb33a8b0c90b8b8594e850f349ecfcd85` — Filter canonical appearances to proven substitutes
- `0e3b30272f697ba8e19b49a41789e36980e44e61` — Regress Brighton unused bench exclusion
- `d77e4b99127b07731cba3f9ff345a48d34cfc5aa` — Make appearance population import-safe
- `07c672f555ac3e59193b1091e4d70a2d1ef04326` — Expose appearance population module to tests
- `f3e6cc65a10f29a2ec11bb8f977aa6af8c0c62c2` — Load appearance validator in source dry run tests
- `63e4a181917b6152a7734cccf5e65e90d2483f0e` — Require appearance validation before promotion
- `ef0060775b87f91d8f01a882b279154b3f59c66f` — Include appearance population in canonical diff fixtures
- `49b82931c19c72f9a8d5fbb35a0c6e86fc9f811a` — Make source-driven fixture benches substitution-complete
- `2f7115a8e43d9c3dc3340951295c4284291d21c3` — Make fully-evidenced fixture benches substitution-complete
- `a33eb274929d6fe881ae43c07ce5af652a91601a` — Require proven substitutes in canonical player matches
- `86776269788e44acde6af3a102b4eee87a26a170` — Lock Brighton canonical appearance regression

The Golden snapshot branch is created only after this handover file is committed, so inspect its branch SHA for the exact immutable snapshot.

## BACKUP / ROLLBACK RULES

Permanent Golden database branch `golden-database-2026-09-06` is NEVER deleted.

Golden production dump:
`~/Documents/LUFC_DATABASE_BACKUPS/GOLDEN_2026-09-06/LUFC_DATABASE_GOLDEN_2026-09-06.dump`
SHA-256: `e10457e505683c73f6e1c84a840a3c7a81e5c2596957d7b0c4a959ea4702e0a0`
Restore test passed 22/22 canonical row counts. Dump contains secrets and MUST NEVER be committed to public GitHub.

Brighton pre-import backup:
`~/Documents/LUFC_DATABASE_BACKUPS/PRE_IMPORT_2026-09-07_BRIGHTON/LUFC_DATABASE_PRE_IMPORT_2026-09-07_BRIGHTON.dump`
SHA-256: `ca1bbcf4e770a093af9ede8cce5e3c0bcfdf34db3c2e58c482d472b3b121a6b5`
Verified with `pg_restore --list`.

Hard rule:

> **NO PRODUCTION IMPORT WITHOUT A VERIFIED PRE-IMPORT BACKUP AND ROLLBACK MANIFEST.**

Rolling pre-import backups: fresh before each production canonical update, retain 14 days. Golden backup excluded from deletion.

## CLOUD SCHEDULER — CURRENT POSITION

The fixture-aware SofaScore scheduler already exists. It rereads provider fixture timing, is event-ID aware, waits for a provider-finished state, supports broadcaster/date moves, and collects raw evidence with zero canonical database writes. Raw capture manifests explicitly assert `database_writes = 0` and `canonical_lufc_ids_assigned = false`.

Do NOT confuse raw collection with production promotion.

Automatic production promotion remains intentionally paused until the complete validation chain is green and reviewed. Scheduled workflow deployment/default-branch behaviour must be checked before claiming the cron is live.

## GOLDEN RULES FOR FUTURE WORK

1. GitHub current branch HEAD is code source of truth. Inspect it before changes.
2. One semantic change at a time. Fetch current blob SHA before GitHub file writes.
3. Never make fixture-specific +1/-1 corrections or hacks.
4. Never silently infer missing historical facts.
5. Never duplicate an authoritative population in frontend code.
6. `player_matches` means players who actually appeared, not the matchday squad.
7. Named unused substitutes never count as appearances.
8. Sub appearance set must exactly reconcile to proven player-on set.
9. Opposition identities stay in opposition namespaces; never contaminate Leeds player IDs.
10. Provider IDs never become canonical LUFC IDs.
11. Raw provider evidence is immutable and preserved.
12. Validation failure means BLOCK, not best-effort import.
13. Production writes require a verified pre-import backup and rollback path.
14. Production UI and signed-off `/test/a1` Match Log remain protected unless user explicitly asks to alter them.
15. Stat Pack is paused/protected; do not casually modify its Golden work.
16. Golden Database Master branch is permanent and must never be deleted.
17. Attendance rule: verified absence is acceptable; unresolved absence is a blocker. Do not infer attendance from capacity.
18. No secrets/passwords/database dumps in public GitHub.
19. After code changes, verify exact Actions run for the resulting HEAD where available; do not treat absence of CI as PASS.
20. Do not weaken validation/tests simply to get CI green.

## KNOWN CI POSITION AT HANDOVER

The latest direct feature-branch commits were not receiving attached workflow runs. Therefore the latest appearance hardening has NOT been declared CI-certified merely because no failure is shown. The next chat should inspect workflow behaviour and run/fix the regression suite without weakening the new gate.

Previous failures were useful: they exposed synthetic fixtures that treated bench membership as sufficient and then exposed the deeper 20-player assumption in `sofascore_canonical_diff.py`. Those assumptions have been corrected.

## REMAINING WORK / NEXT PRIORITIES

Do not over-audit Brighton again unless new evidence appears. The production repair and principal downstream surfaces have been checked.

Next priorities:
1. Inspect the exact Golden snapshot/current working HEAD and this handover.
2. Get the full pytest/build validation green for the new appearance contract; fix stale fixture expectations, never the rule.
3. Add/finish a durable Brighton rollback manifest if it is not already present, including the five transient erroneous player_match IDs and their corrective deletion.
4. Resume the raw-capture → staging → validation → proposed-diff chain.
5. Keep production promotion manual/`READY FOR REVIEW` initially.
6. Automate mandatory pre-import backup verification before any promotion.
7. Verify scheduler/default-branch deployment before claiming automated cron is live.
8. After a meaningful clean run of future fixtures, consider whether promotion can safely become more automatic.

## SECURITY / SEPARATE AUDIT

A prior audit found public Supabase tables with RLS disabled. This is a separate security project. Do not casually enable RLS during ingestion work; audit policies and application impact first.

## USER WORKING STYLE / CONTINUITY

The user wants the engineering handled autonomously. When they say “keep going”, “push”, or similar, continue the agreed pipeline rather than repeatedly asking what to do next. Keep milestone updates concise. Do not make the user use Terminal unless unavoidable. Never ask them to paste database passwords/secrets into chat.

The user values forensic accuracy over speed and prefers a blocked import to a plausible-but-wrong database update.

## THE POINT WE REACHED

The Brighton bug was not merely patched. Its root assumption was identified and changed across source validation, canonical diff construction, promotion gates and permanent regression tests.

The permanent lesson is:

> **A MATCHDAY SQUAD IS NOT AN APPEARANCE POPULATION.**
>
> **11 STARTERS + PROVEN PLAYERS-ON = CANONICAL APPEARANCES.**
>
> **ANY DISAGREEMENT BLOCKS PROMOTION.**

Preserve this Golden Moment.