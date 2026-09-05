# LUFC DATA V2 — MASTER HANDOVER
## Status: 5 September 2026
## Repository: `lufcdata/LUFC-Data-V2`
## Active branch: `ui-bolt-opponents-v1`
## Supabase project: `nztiaxnrwojraiwipwjj`
## Live app: `https://lufc-data-v2.onrender.com/`

This document hands the project to a new ChatGPT conversation. It supplements, and does not supersede, the earlier authoritative handovers:
- `docs/HANDOVER_SEPT_2ND_2026.md`
- `docs/HANDOVER_SEPT_3RD_2026_PLAYER_STATS_GOLD.md`

**FIRST ACTION IN A NEW CHAT:** inspect current GitHub `ui-bolt-opponents-v1` HEAD and read all three handovers before changing anything. At handover creation the branch HEAD was `b8b5bf37cb7c1b5ab09f3b3c0e628b5c8c2210b2` (`Restore original Test A1 Match Log styling`). This SHA will move when this handover is committed, so GitHub remains the source of truth.

---

# 1. GOLDEN RULES — MANDATORY

1. **Inspect GitHub HEAD before every repository write.** Never assume the branch is where the previous message left it.
2. Read the Sept 2, Sept 3 Player Stats Gold, and this Sept 5 handover before substantial work.
3. Inspect relevant live Supabase state before schema/data changes.
4. Supabase is the data source of truth. The current signed-off UI is the visual source of truth.
5. **One fact → one authoritative source → every surface in sync.**
6. Never invent IDs, dates, stats, ranks, positions, honours, match facts, shirt numbers, line-ups, or provenance.
7. Join by canonical IDs, never by names when an ID exists.
8. Never use +1/-1 hacks, fixture-specific corrections, or target-fit data to match an external source.
9. External databases are evidence, not targets. Investigate fixture-level facts when totals disagree. The Norman Hunter European appearance audit is the model example.
10. User visual verification is required before changed production UI is called Gold.
11. Supabase queries capable of returning >1,000 rows must paginate or aggregate server-side.
12. `player_spells` is a canonical first-class integrity layer; preserve distinct spells.
13. Golden recovery branches are recovery only, not active development sources.
14. **Do not add players outside the existing 902-player universe.**
15. Protect signed-off Player Stats / Player Page. Mobile Player Page was explicitly approved with: “Okay perfect on mobile now. Don't touch that.” Only make explicitly requested scoped changes.
16. Historical unavailable assists remain `—`, never silently zero.
17. Played Alongside must paginate.
18. Never call an experimental Test page production Gold unless the user explicitly signs it off.

---

# 2. CORE DATABASE / APP STATE

Protected baseline previously verified:
- matches: 4,856
- seasons: 101
- clubs: 190
- actual clubs faced: 169
- players: 902
- managers: 49
- manager_spells: 57
- player_matches: 58,528
- goals: 7,282
- match_substitutions: 5,112
- player_spells: 943
- distinct spell players: 902
- open/current player_spells: 26

Reference Match Centre fixture:
**Match #4846 — Manchester United 1–2 Leeds United, 13 April 2026.**

Live Render deployment known-good configuration:
- Auto-Deploy: After CI Checks Pass
- Workspace Overlapping Deploy Policy: Wait
- Root Directory: `frontend`
- Publish Directory: `dist`
- `NODE_VERSION=20.20.2`
- `SKIP_INSTALL_DEPS=true`
- `NPM_CONFIG_PREFER_OFFLINE=true`
- `NPM_CONFIG_AUDIT=false`
- `NPM_CONFIG_FUND=false`
- Build: `npm ci && npm run build`
- GitHub CI caches `frontend/node_modules` keyed by `frontend/package-lock.json`
- known-good deployment benchmark ~23.8s
Do not casually change this configuration.

Approved visual language:
- yellow `#F2E01F`
- blue `#2F91ED`
- cyan `#50E5E0`
- loss/red pink `#F73475`
- light primary dark text `#15192B`
- dark page historically `#0d0e19`
- typography: Manrope, DM Mono, Urbanist
Prefer scoped CSS.

---

# 3. MATCH CENTRE

Main files:
- `frontend/src/MatchCentre.tsx`
- `frontend/src/MatchCentre.css`
- `frontend/src/MatchCentreSquad.css`
- `frontend/src/MatchCentreDetails.css`
- `frontend/src/Matches.tsx`
- `frontend/src/App.tsx`

Matches rows open Match Centre using canonical `match_id`. Home/away hero order uses canonical `venue_type`.

Match Centre milestones are live through:
- `public.match_centre_milestones`
- RPC `public.get_match_centre_milestones(p_match_id integer)`
- migration `supabase/migrations/20260904111000_add_match_centre_milestones_rpc.sql`

For #4846 canonical facts include Manchester United 1–2 Leeds, HT 0–2, Old Trafford, 74,018, referee Paul Tierney, 8:00 PM, 3-4-1-2, Daniel Farke, Michael Carrick, captain Ethan Ampadu, MOTM Noah Okafor, Okafor goals 5 and 29, Casemiro 69, Lisandro Martínez red 56.

Opponent scorer parsing was hardened for repeated minutes, penalties, phase-only strings, unavailable exact minutes, and safe HT/FT inference without inventing facts.

---

# 4. MANAGER PROFILES

Manager profiles are implemented in Player-profile visual language and use canonical manager IDs.

Main files include:
- `frontend/src/ManagerPage.tsx/.css`
- `ManagerInformation.tsx`
- `ManagerCareerMetrics.tsx`
- `ManagerCompetitionBreakdown.tsx`
- `ManagerPerformanceRadar.tsx/.css`
- `ManagerProfileBreakdowns.tsx/.css`
- `ManagerDebutantsTable.tsx/.css`
- `ManagerSeasonLog.tsx`
- `ManagerMatchLog.tsx`

Source enrichment: `public.manager_spell_profile_enrichment` (57 rows loaded).
RPCs:
- `get_manager_profile_metrics`
- `get_manager_performance_radar`
- `get_manager_profile_breakdowns`
- `get_manager_debutants_detail`

Current profile flow: hero → top stats → Career Background → radar → managerial record + competition breakdown → analysis widgets → Debutants → Season Log → Manager Match Log.

Manager table filters: Competition → Venue → Nationality → Permanent → +5 Matches → Search.

---

# 5. SHIRT-NUMBER SYSTEM — COMPLETE END TO END

## Historical semantics
### 1991/92 and 1992/93
Numbers were not fixed. Store **match-level facts**:
`match_id → player_id → shirt_number`.
Never collapse these into fake season-level squad numbers and never infer missing values.

### 1993/94 onward
Persistent/fixed official squad-number era:
`season → player_id → squad_number`.
Number reuse after departures is legitimate. Official squad assignment is semantically distinct from actual match-worn number because Leeds sometimes reverted to 1–11 in domestic cups. Preserve that distinction in canonical data.

## Canonical tables
`public.player_match_shirt_numbers`
- 1,409 rows total
- 1991/92: 635 canonical rows / 49 matches
- 1992/93: 774 canonical rows / 55 matches
- PK `(match_id, player_id)` and unique `(match_id, shirt_number)`

`public.player_season_squad_numbers`
- 1,152 rows
- one null/TBC: Michael Zetterer 2026/27
- no duplicate `(season_id, player_id)` groups

Unified read layer:
`public.shirt_number_assignments`
- `fact_type='match_worn'` for 1991/92–1992/93
- `fact_type='official_squad'` for 1993/94 onward

RPCs:
- `get_player_shirt_number_history(p_player_id bigint)`
- `get_shirt_number_wearers(p_shirt_number smallint)`

Important migrations/commits already exist for canonical layers, unified reads, six missing canonical assignments, 17 exact player-season gaps, and provenance.

## Closed player universe
No players were added. Source-only noncanonical players are retained in provenance but excluded from canonical player facts. Important examples:
- Ally Mauchlen: 2 source rows in 1991/92, excluded
- Paul Pettinger: 1 source row in 1992/93, excluded

## Canonical reconciliation
Six initially missing canonical assignments were independently verified:
- Steven Caldwell #15 2003/04
- Sam Vokes #15 2009/10
- Mika Vayrynen #7 2011/12
- Andros Townsend #17 2011/12
- Paul Robinson (DF) #33 2011/12
- Marius Zaliukas #24 2013/14

A stronger player-season audit found and reconciled 17 more exact gaps:
- Lee Sharpe #7 1998/99
- Darren Huckerby #12 2000/01
- Mike Grella #13 2008/09
- Aidan White #32 2009/10
- Davide Somma #27 2009/10
- Enoch Showunmi #21 2009/10
- Sanchez Watt #24 2009/10
- Aidan White #32 2010/11
- Andy O’Brien #40 2010/11
- Ben Parker #19 2010/11
- Scott Wootton #22 2013/14
- Ronaldo Vieira #37 2015/16
- Barry Douglas #3 2020/21
- Mateusz Bogusz #44 2020/21
- Robbie Gotts #36 2020/21
- Cody Drameh #37 2021/22
- Helder Costa #17 2021/22

Critical audit lesson: **derive season from canonical `matches.season_id`, never calendar date.** Pandemic-delayed July 2020 fixtures proved why.

Final exact post-1993 player-season appearance combinations missing a squad assignment: **0**.

## Raw provenance archive — COMPLETE
This was the final outstanding shirt-number task and is now complete.

Raw uploaded sources preserved:
- 1991/92: 637 rows
- 1992/93: 775 rows
- 1993/94–2026/27: 1,322 rows
- total raw uploaded source rows: **2,734**
- supplemental independently verified rows: **23**
- total provenance records: **2,757**
- unresolved provenance rows: **0**

Resolution:
- 1991/92: 635 canonical, 2 Ally Mauchlen excluded
- 1992/93: 774 canonical, 1 Paul Pettinger excluded
- fixed source: 1,129 rows resolve to canonical players; 193 source rows belong outside the closed 902-player universe and remain provenance-only
- canonical match-level facts linked to provenance: **1,409 / 1,409**
- canonical fixed-era assignments linked to provenance: **1,152 / 1,152**
- the 1,152 fixed assignments = 1,129 from authoritative CSV + 23 independently verified supplemental omissions
- 62 obsolete `canonical_assignment_audit` comparison artefacts were removed; they were not genuine source provenance and were not referenced by canonical facts
- deterministic source fingerprints were established so source drift is detectable

Important provenance lesson: a re-uploaded final source exposed older archived sections (notably part of 2001/02–2004/05 and the tail of 1991/92). The solution was deterministic raw-row comparison and exact replacement, never reconstruction or guessing.

GitHub provenance commits from the completed workstream:
- `ddd77ef98f76720b2ecb37172ae17dc147a65d70` — Track shirt number provenance schema
- `d6be001189c9e599faa24bada6138178801c1685` — Finalize shirt number provenance archive

## Player Profile shirt-number UI
`frontend/src/PlayerShirtNumberHistory.tsx/.css`
Current panel is deliberately simple:
- Shirt Number
- Appearances
It aggregates career usage by number. Early-era counts only rows that correspond to actual `player_matches`, so unused subs are not appearances. Fixed-era seasons use canonical appearance counts under the official season assignment. Same number across seasons is summed.

Semantic warning: a fixed-era number with 0 appearances does **not automatically mean** the player was an unused substitute in that number. Match-level unused-sub evidence exists explicitly only where the source records it (especially 1991/92–1992/93). Do not conflate official assignment with match-worn fact.

## Match Centre shirt numbers
Commit `fbad3a02cdca3663efcf7d5e437660b947d3f857` wired shirt numbers into squads.
Logic:
- fetch canonical match `season_id`
- fetch `player_season_squad_numbers`
- fetch `player_match_shirt_numbers`
- season official number loads first; match-level number overrides
Thus 1991/92–1992/93 display actual match-specific numbers; 1993/94 onward display official season assignments.

Current fallback in Match Centre historically used `shirtNumbers.get(id) ?? p.lineup_order`. This is not semantically ideal if a canonical number is genuinely absent/TBC. If hardening later, use `—` when a number is expected but missing; do not treat `lineup_order` as authoritative shirt number.

---

# 6. PLAYER STATS EUROPE / INTER-CITY FAIRS CUP FIX

Bug: `filtered_player_leaderboard(p_filter,p_venue)` used `Inter-Cities Fairs Cup`, while canonical matches use `Inter-City Fairs Cup`, excluding the competition from Europe totals.

Fix recognizes both spellings and excludes the special 1971 Trophy Play-Off semantically using Fairs Cup + `round='PO'`.

Why exclude the PO? Match #2072, Barcelona 2–1 Leeds, 22 Sep 1971, was the special Inter-Cities Fairs Cup Trophy Play-Off for permanent possession of the old trophy after UEFA took over; it is not treated as a normal competitive European fixture in the project convention.

Migration: `supabase/migrations/20260905030000_fix_player_stats_europe_fairs_cup.sql`
Commit: `245c1d28820e9ec94ce68110aac23540a4ac95f7` — Fix Player Stats Europe Fairs Cup filter

Post-fix live totals included:
- Billy Bremner 76 European apps, 16 goals
- Norman Hunter 78 apps, 1 goal
- Paul Reaney 76 apps, 0 goals
- Peter Lorimer 74 apps, 30 goals

## Norman Hunter “phantom appearance” — RESOLVED, DO NOT CHANGE
External RSSSF individual totals suggested Hunter 77, while LUFC Data had 78. We did **not** target-fit to 77. Fixture-level investigation found the likely external omission in the 1969/70 European Cup quarter-final against Standard Liège.

LUFC Data has Hunter starting all six of these 1969/70 European Cup fixtures in the relevant run:
- 17 Sep 1969 Lyn Oslo home
- 12 Nov 1969 Ferencváros home
- 26 Nov 1969 Ferencváros away
- 4 Mar 1970 Standard Liège away
- 18 Mar 1970 Standard Liège home
- 15 Apr 1970 Celtic away

Independent lineup evidence supported Hunter in **both** Standard Liège 1–0 wins. The external career compilation appears to omit one of the two same-score Standard fixtures. Therefore **our 78 remains canonical and no player_matches mutation was made.**

This is a core project lesson:
> External sources are evidence, not the target. When totals disagree, audit the underlying fixtures and line-ups. Our data must be able to prove its totals.

The project shorthand that emerged: **OUR DATA IS KING.**

---

# 7. TEST A1 — CURRENT EXPERIMENTAL UI WORKSTREAM

The user asked to trial a new isolated page named **Test A1** based on a premium Football Manager-style dashboard screenshot, using Billy Bremner as the test player. The user explicitly said **do not adjust UI/design across the app**. This is experimental only and must remain isolated from the protected Player Page.

Main files:
- `frontend/src/TestA1.tsx`
- `frontend/src/TestA1.css`
- `frontend/src/App.tsx` exposes Test A1 in navigation/routing

Initial concept commits included:
- `eee78b8f...` Add isolated Test A1 player dashboard
- `db80c94b...` Style isolated Test A1 player dashboard
- `872f7daa...` Expose isolated Test A1 page

Billy Bremner is canonical player ID **276**, legacy number **276**.

Initial Test A1 structure:
- top feature/profile area: profile icon, Billy Bremner name/full name, Scotland flag + declared nation, DOB, career, positions, legacy number
- Appearance Ranking panel modelled on screenshot “Standing”; Billy ranks 2nd with 772 appearances behind Jack Charlton 773
- right column Match Log backed by canonical `player_matches` + `match_centre_summary`
- compact Player Stats, Career Record, Leeds Career panels
- only the decorative career-record bar graphic was intentionally non-data visual texture

User reaction to first Test A1: **“Wow! I think this is epic!”** This is strong approval of the overall direction, but not formal Gold sign-off.

## Latest requested profile-area visual change
The user then asked the top profile section to:
- remove the second/right-side profile portrait
- remove the `LUFC` lettering
- remove the coloured/lined hero background
- make the profile section the same colour as the rest of the screen

Inspect current `TestA1.tsx` and `TestA1.css` before assuming whether all of these are already applied; GitHub HEAD is authoritative.

## Match Log addition request and immediate rollback
The user briefly asked to add to Test A1 Match Log:
- `goals2.png`
- `Captain Icon3.png`
- `Red Card Icon2.png`
- screenshot-style up/down arrows for sub on/off with minute, e.g. arrow + 79

**Then the user immediately said: “Please undo the additions to the Match log.”**

That rollback has already been committed. At handover creation the branch HEAD is:
`b8b5bf37cb7c1b5ab09f3b3c0e628b5c8c2210b2` — **Restore original Test A1 Match Log styling**.

Therefore the next chat must **NOT re-add the goal/captain/red-card/substitution icon additions unless the user explicitly asks again.** The Match Log should be treated as restored to its original Test A1 presentation.

This latest rollback is the exact current point of work.

---

# 8. REPOSITORY HYGIENE / HISTORICAL QUIRKS

Two accidental branches were created earlier while accessing GitHub tooling:
- `temp-no`
- `temp-no2`
They contained no intentional code changes and pointed at an existing commit. If branch deletion capability becomes available and they still exist, they may be cleaned up. Do not let them become development sources.

Experimental Test/Test2/Test3 pages from an older phase were deleted; only the newly requested Test A1 experiment should be considered active.

App defaults to Matches. Existing production pages remain Matches, Match Centre, Players, Player Profile, Managers, Manager Profile, Opponents, plus isolated Test A1 experiment.

---

# 9. WORKFLOW / PIPELINE FOR FUTURE CHANGES

For any new task:

1. **Inspect active branch HEAD.**
2. Read relevant handover(s).
3. Fetch/inspect the exact files involved.
4. If data-related, inspect live Supabase schema and canonical rows first.
5. State/understand the semantic source of truth before writing.
6. Make the smallest scoped change possible.
7. Do not modify protected data/UI layers unless explicitly requested.
8. For database changes, use migrations and commit corresponding migration SQL to GitHub.
9. For UI, consume canonical IDs/data rather than duplicating facts in frontend constants.
10. Validate with known canonical examples and edge cases.
11. Re-inspect HEAD immediately before the repository write.
12. Build/CI/deploy should use existing known-good pipeline.
13. User visually verifies UI before Gold designation.
14. If an external total disagrees, investigate fixture-level evidence rather than forcing our data to match it.
15. For source imports/provenance, preserve raw evidence and distinguish exclusions/supplemental evidence honestly.

---

# 10. CURRENT NEXT STEP

The conversation ended immediately after the user asked for this handover. The last functional action before the handover was the **Test A1 Match Log rollback**, already represented by HEAD `b8b5bf37...` before this document commit.

A new chat should begin by saying it has inherited this handover, then:
1. inspect current `ui-bolt-opponents-v1` HEAD;
2. read `docs/HANDOVER_SEPT_2ND_2026.md`;
3. read `docs/HANDOVER_SEPT_3RD_2026_PLAYER_STATS_GOLD.md`;
4. read this `docs/HANDOVER_SEPT_5TH_2026.md`;
5. inspect current `TestA1.tsx` / `TestA1.css` if continuing Test A1;
6. make **no changes until current repository state is understood**.

The production data architecture is in a strong state: shirt numbers are canonical and provenance-complete, the Europe/Fairs Cup bug is fixed, Norman Hunter’s 78 European appearances survived forensic audit, and Test A1 remains an isolated UI experiment.

**OUR DATA IS KING.**
