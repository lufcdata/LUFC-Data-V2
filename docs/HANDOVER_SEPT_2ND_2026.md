# LUFC DATA V2 — HANDOVER SEPT 2ND 2026

**Status:** 2 September 2026  
**Repository:** `lufcdata/LUFC-Data-V2`  
**Live Supabase project:** `nztiaxnrwojraiwipwjj`  
**Current production UI branch:** `ui-bolt-opponents-v1`  
**Leeds Managers research branch:** `leeds-managers-gold-v1`

> This document is the authoritative continuity handover for the next ChatGPT conversation. Future handovers must inherit this document and all later handovers rather than starting from scratch. Inspect the current GitHub branches and live Supabase state before changing anything, because code/database state may have advanced after this note.

---

## 1. PRIMARY WORKING INSTRUCTION

This is an active Leeds United historical database, data-engineering and product project. The user expects autonomous continuation with concrete repo/database/research/UI work whenever they say **keep going**, **go**, **go for it**, **let's commence**, **home run**, **yes please**, etc. Do not respond with planning-only prose when the requested work can actually be performed.

The central product principle is:

> **ONE FACT → ONE AUTHORITATIVE SOURCE → EVERY SURFACE IN SYNC.**

The product goal is an interconnected Leeds United football history. Match, season, competition, opponent, player, manager, goal, substitution and future official/stadium entities should be relational and reusable. UI surfaces display canonical truth; they do not invent it.

---

## 2. NON-NEGOTIABLE GOLDEN RULES

1. Never destroy source truth.
2. No silent semantic rewrites.
3. Canonical normalized tables are application truth; preserve raw source.
4. Never use generated IDs to join unless the source actually contains them.
5. Validate after every meaningful mutation.
6. User verification is mandatory before Gold signoff.
7. Do not modify unrelated football repositories.
8. No fixture-specific hacks, guessing or +1/-1 target-fitting.
9. Fixture assignment is higher priority than exact tenure dates, but the researched Managers CSV dates are presumed highly accurate and must be protected.
10. Do not invent dates to fill gaps.
11. Exact spell dates and caretaker/interim/permanent labels are enrichment; the primary Gold target is correct authority for all 4,856 fixtures.
12. Raw source strings remain untouched even when canonical identity/authority is corrected.
13. Shared/joint authority only where evidence explicitly supports shared first-team control.
14. Do not rebuild completed/signed-off Gold layers.
15. **Opposition Managers is GOLD LOCKED.**
16. Leeds Managers rule: **ONE LEEDS MATCH → ONE AUTHORITATIVE LEEDS MANAGERIAL ASSIGNMENT.**
17. Committee/board authority must not be modeled as a fictional person.
18. Caretaker-to-permanent transitions require role periods if the same manager later became permanent.
19. Repo discipline: finish layer → Gold approval → integrate into `main` → create next work branch from updated `main`.
20. Managers CSV exact dates are the project researched baseline.
21. Administrative appointment date does not automatically determine fixture ownership.
22. UI/product: one canonical fact drives every surface.
23. Major entities should be clickable/linked wherever practical.
24. Match Centre is the heart of the product.
25. Data truth and presentation are separate: canonical/Gold data remains protected while UI can iterate.
26. **BOLT UI = VISUAL SOURCE OF TRUTH. SUPABASE = DATA SOURCE OF TRUTH.** Do not freestyle/reinterpret the supplied Bolt design.
27. Old generic UI was rejected and must not be merged/reused.
28. Club/manager imagery should have one authoritative reference and be reused across surfaces.
29. Do not knowingly create partial/ambiguous crest/icon state.
30. Future ChatGPT handovers must include this handover and subsequent changes so project context is cumulative, not lossy.

---

## 3. REPOSITORY / BRANCH STATE

Repository: `lufcdata/LUFC-Data-V2`.

Known consolidated `main` state before current UI work:
- integration merge `c070632b4cbb027b8f0015f6aa7b70debc6d1c95`
- housekeeping commit `e50e3bfbcd60713e52822bc43e1f9ef86b658106`
- repository state document: `docs/REPOSITORY_STATE_2026-09-01.md`

Important branches:
- `main` — consolidated source of truth for completed layers.
- `leeds-managers-gold-v1` — Leeds Managers forensic research/Gold engineering branch. Research is advanced but NOT user-signed-off Gold.
- `ui-bolt-opponents-v1` — active production UI branch and current Render branch.
- `ui-opponents-v1` — rejected old generic UI branch; quarantined/unmerged. User wants it deleted when safe branch deletion capability is available.
- `ui-opponents-v1-test` — accidental empty branch; also delete when safe.
- `ui-club-crest-images-v1` — temporary image upload branch used during crest work; production work moved back to `ui-bolt-opponents-v1`.
- `ui-crest-hq-staging` — old crest staging branch; quarantined.

Never claim rejected branches have been deleted unless deletion is actually confirmed.

---

## 4. LIVE BASELINE DATA COUNTS

Known live baseline:
- matches: **4,856**
- seasons: **101**
- clubs: **190** total club rows
- distinct opponents actually appearing in the 4,856 matches: **169**
- players: **902**
- managers: **49**
- manager_spells: **57**
- player_matches: **58,528**
- goals: **7,282**
- match_substitutions: **5,112**

Do not describe all 190 club rows as opponents; the Opponents UI is based on the 169 clubs actually faced.

---

## 5. COMPLETED / PROTECTED DATA LAYERS

Do not rebuild these casually:
- core schema/import
- clubs/seasons
- 4,856 matches
- 902 players
- 7,282 goals
- 58,528 player_matches
- match core Gold
- substitutions Gold — 5,112 rows
- match enrichments
- club reconciliation
- **Opposition Managers GOLD LOCKED**

### Opposition Managers Gold summary
Final live reconciliation:
- match_count = 4,856
- assignment_count = 4,856
- distinct_assignment_matches = 4,856
- individual = 4,810
- joint = 15
- committee = 31
- forensically_validated = 130
- missing = 0
- raw_mismatch = 0
- canonical_mismatch = 0
- authority_mismatch = 0
- malformed_joint = 0
- malformed_individual = 0

User directly verified examples including Gary Megson 6 May 1995, Billy Dougall 23 Nov 1957, Christian Gross 4 Mar 1998, Colin Lee 7 Aug 2005 and Iffy Onuora + Mick Docherty joint caretakers 29 Sep 2007.

Gold audit commit: `889bd6496edd47dff8f80def4be4e02b7977a6d1`  
Audit: `docs/OPPOSITION_MANAGERS_GOLD_AUDIT_2026-09-01.md`

Live relational opposition-manager tables include:
- `managerial_people`
- `managerial_person_nationalities`
- `managerial_committees`
- `managerial_assignments`
- `managerial_assignment_people`
- `opposition_manager_spells`
- `opposition_manager_role_periods`

---

## 6. LEEDS MANAGERS — RESEARCH STATE

Branch: `leeds-managers-gold-v1`  
Audit: `docs/LEEDS_MANAGERS_GOLD_AUDIT_2026-09-01.md`  
Initial audit commit: `a9bc33fdb1973476650dd4a2c1a427288556b1d9`

Chronological research is complete through Daniel Farke, but engineering/Gold integration is unfinished and must NOT be called Gold until user approval.

Current relevant schema:
- `matches.manager_spell_id bigint nullable`
- `managers`: manager_id, canonical_name, full_name, DOB, place_of_birth, DOD, declared_nation, profile_image_url, did_you_know, awards, created_at
- `manager_spells`: manager_spell_id, manager_id, legacy_manager_order, role, date_joined, date_left, caretaker, status, source_manager_name

Key forensic conclusions:
- 1935 Board Committee, Ernest Pullan lead.
- Bill Lambton continuous authority 10 May 1958–9 Mar 1959 with role-period distinction.
- Bob Roxburgh: 9 fixtures, sole principal authority.
- 5 Oct 1974 Arsenal: Maurice Lindley operational authority.
- 1980 Lindley caretaker; no David Merrington.
- Eddie Gray player-manager from July 1982.
- O'Leary: one continuous spell with caretaker → permanent role periods.
- Reid caretaker/interim then permanent.
- Blackwell caretaker then permanent.
- 24 Oct 2006 Southend: Dave Geddis; Wise not involved.
- 29 Jan 2008 Southend: Gwyn Williams; McAllister first fixture 2 Feb.
- 18 Feb 2012 Doncaster: Redfearn fixture authority despite Warnock appointment.
- 1 Feb 2014 Huddersfield: Nigel Gibbs fixture authority within continuous McDermott legal tenure.
- 2023 Skubala: principal interim boss, not joint.
- Gracia appointed 21 Feb, visa 24 Feb, first game 25 Feb.
- Farke PASS.
- Baseline coverage: 4,856/4,856 assigned, 57 distinct spells, no out-of-range assignment.

Future matchday-leadership enrichment approved conceptually AFTER Leeds Managers Gold:
- manager_of_record
- matchday_lead
- absence_reason
- absence_type
- team_selection_authority

No `manager_present` field.

---

## 7. PRODUCT / UI SOURCE OF TRUTH

React/Vite frontend. Intended product areas:
- Home/Dashboard
- Matches archive
- Match Centre
- Players / Player Centre
- Managers / Manager Centre
- Seasons / Season Centre
- Clubs/Opponents / H2H Centre
- Competitions likely first-class
- Officials/Stadium possible later

Initial vertical slice was **Opponents → Opponent Centre → Match Centre**. Current work has expanded to a new **Managers** page.

The supplied Bolt UI is the actual visual source of truth. The user strongly rejected a generic redesign. Reuse the established components/CSS and surgically replace dummy data with Supabase-backed data.

Typography:
- Manrope
- DM Mono
- Urbanist additions approved for page titles/team/manager names

Global approved color rules:
- former orange accents → `#F2E01F`
- dark-grey non-text accents → `#2F91ED`
- Win % bars → `#50E5E0`
- Loss % bars → `#F73475`
- Last 5 Won → `#89F0DD`
- Last 5 Drawn → `#F0CA7D`
- Last 5 Lost → `#E6739B`
- text colors otherwise remain design-driven

Render:
- project/site: `LUFC Data V2` / `LUFC-Data-V2`
- branch: `ui-bolt-opponents-v1`
- root: `frontend`
- build: `npm install && npm run build`
- publish: `dist`
- live URL: `https://lufc-data-v2.onrender.com`
- env vars: `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`
- browser uses publishable key only; never service-role key.

If runtime breaks, inspect the actual browser/runtime error first rather than making speculative redeploys.

---

## 8. OPPONENTS PAGE — USER-APPROVED STATE

The user explicitly called the current table/filter state perfect. Do not gratuitously redesign it.

Controls:
Competition:
- All
- League
- Premier League
- FA Cup
- League Cup
- Europe

Venue (separate selectable group):
- All
- Home
- Away
- Neutral

Other controls:
- `+5 Matches` toggle
- search
- all controls combine

Live venue totals previously validated:
- Home 2,409
- Away 2,402
- Neutral 45
- Total 4,856

`filtered_opponent_leaderboard(p_filter, p_venue)` is the Supabase RPC backing combined filters.

Base columns:
- #
- Opponent
- P
- W
- D
- L
- GF
- GA
- GD
- GPG
- CS
- Win %
- Loss %
- Last Played
- Last Won
- Last Lost
- Last 5

Premier League filter only additionally shows `Pts` after L, calculated as W×3 + D. It disappears on non-PL filters and is included in the legend only on PL.

GD behavior:
- number remains standard text color
- positive GD BAR = Win color `#50E5E0`
- negative GD BAR = Loss color `#F73475`
- zero = neutral
- active/sorted heading = `#2F91ED`

Dynamic top-right header count now displays e.g. **4,856 Matches Selected** and updates from the currently visible/selected rows. The user confirmed it is visible and working.

Important recent count fix commits included `d5ed55f7238fb32239bdb1f640439c1dec9ddafc` and `7076d45d27c4ef3bf1b94f8582059992a1972ae2`.

---

## 9. LIGHT / DARK MODE

Implemented on `ui-bolt-opponents-v1`.

Light is default on fresh load. A Sun/Moon toggle is in the hard top-right corner.

Dark requested primary values:
- page background `#0d0e19`
- card/text-container background `#1d2438`
- default dark font `#F5F5F5`

Commits included:
- `d5e34549774e6a4d94720aa9be890f28a4356301`
- `74cb2e9a0e80b9fde4731e314efc60e06b33460c`

No localStorage persistence yet; fresh load starts light. Do not claim theme persistence.

---

## 10. CLUB CRESTS — RESOLVED

The sprite/HQ approach was abandoned. User manually uploaded all 169 PNGs and the frontend uses direct normal `<img>` files. User confirmed this worked well.

Current rule: use direct PNGs and placeholder only when missing. Do not return to sprite architecture unless explicitly requested.

Canonical filename variants were handled for names including Ankaragücü, Derby County, Grasshopper Zürich, Metalurg Zaporizhzhya, Vitória Setúbal, West Bromwich Albion, Napoli and Southend United.

---

## 11. MANAGERS PAGE — NEW ACTIVE WORK

A new **Managers** page has been created on `ui-bolt-opponents-v1`, deliberately replicating the approved Opponents page visual language rather than inventing a new design.

Navigation now has `Opponents` and `Managers` controls.

Initial Managers table columns:
- Manager
- P
- W
- D
- L
- GF
- GA
- GD
- Win %
- Loss %
- First Match
- Last Match

A Supabase `manager_leaderboard` read view was created from manager → manager_spells → matches. This is a presentation/read layer and does NOT make Leeds Managers Gold.

The Managers page now replicates the Opponents filter structure:
Competition:
- All
- League
- Premier League
- FA Cup
- League Cup
- Europe

Venue:
- All
- Home
- Away
- Neutral

Plus:
- `+5 Matches` toggle
- manager search
- dynamic Matches Selected count
- same styling/spacing/fonts/selected states

A Supabase RPC `filtered_manager_leaderboard(p_filter, p_venue)` was created so managerial statistics genuinely recalculate by Competition × Venue rather than buttons being cosmetic.

Relevant UI commits during page creation/filter work include:
- `d4b09e2e63dcc1d4d4e8b36cfe3bcd0a3102108d`
- `c5c799b98f04903f96524caf16f26e5c658b682a`
- `77320aa8f07466e8dd40134219f6a20a42c99774`
- `5a60232c9953406afbfcb99dfacb4ce2bba318c5`

---

## 12. MANAGER ICONS — UPLOADED AND CONNECTED

User uploaded manager PNGs to:

`frontend/public/managers/`

on `ui-bolt-opponents-v1`.

A new component was created:

`frontend/src/ManagerIcon.tsx`

It displays real uploaded manager icons at the same 25×25 visual footprint as opponent crests and falls back to initials only if an image genuinely fails.

Explicit filename exceptions currently include:
- `Bill Lambton` → `Bill Lambton.png`
- `The Board Committee` → `Leeds United Committee.png`
- `Eddie Gray` → `Eddie Gray Icon 1982.png`
- `Jesse Marsch` → `Jesse Marsh Icon.png`
- `Uwe Rösler` → `Uwe Rosler Icon.png`

Do not casually rename user image assets. Prefer explicit mapping when filenames differ from canonical database names.

Manager icon commits:
- `660db13f2fb3151e3a5e9da5df08ae155cf7d5e2`
- `ce5f51ccb860b980a402852ae1c0a29b14ca061e`
- `ca2d2d6655c5cefe8dc419c15c55f704d29a825c`

---

## 13. NATIONALITY FLAGS — IMMEDIATE NEXT TASK

User has also uploaded flag PNGs to:

`frontend/public/flags/`

The flag folder has been confirmed to exist and contains national flags such as England, Scotland, Argentina, Germany, Spain, USA and others.

A live Supabase inspection showed `managers.declared_nation` currently NULL for all 49 manager rows. **However, the user has now explicitly corrected this context: `Managers.csv` contains a `Declared Nation` column.**

Therefore the immediate next task is:

1. Locate/read the authoritative `Managers.csv` used by this project.
2. Extract `Declared Nation` exactly as supplied; do not infer nationalities from general knowledge.
3. Reconcile CSV manager identity to canonical `managers` rows carefully.
4. Populate the canonical `managers.declared_nation` field from that source after validating the mapping.
5. Map each canonical nationality to the actual uploaded file in `frontend/public/flags/`.
6. Add the flag to the Managers UI cleanly, preferably driven from the canonical `declared_nation` field so it can be reused later in Manager Centre/Match Centre.
7. Validate missing/unmatched managers and flags before calling the integration complete.

The user specifically said: **“In Managers.csv there is a 'Declared Nation' column”** and then **“Please continue with these manager icons and flag icons.”** This is the exact continuation point.

Do NOT guess nationality values. The CSV is the source.

---

## 14. CURRENT MANAGER ICON / FLAG DESIGN INTENT

Manager icons should replicate the clean opponent-crest treatment: image beside the canonical manager name, compact and aligned with the table row. Flags should be integrated without disrupting the approved dense table aesthetic. Preserve the existing Urbanist manager name and DM Mono/stat typography.

The manager page should remain visually in sync with Opponents. New design choices should be incremental and based on user feedback, not wholesale redesigns.

---

## 15. MATCH CENTRE READ LAYERS ALREADY AVAILABLE

Known read views:
- `match_centre_summary` — 4,856
- `match_centre_players` — 58,528
- `match_centre_goals` — 7,282
- `match_centre_substitutions` — 5,112

These are future building blocks for the interconnected Match Centre.

---

## 16. USER WORKING STYLE / PRODUCT EXPECTATION

The user values forensic accuracy, fast concrete progress and strong repo discipline. They are enthusiastic when work is correct and visibly integrated, but understandably frustrated by speculative retries, generic redesigns, or loss of project context.

Key interaction rules:
- “keep going” means continue actual work.
- Do not ask routine permission for obvious next steps.
- Report concrete discoveries, mutations, validation and commit IDs.
- Celebrate achievements without falsely labeling unfinished layers Gold.
- User verification is required for Gold.
- Be precise about what is local, GitHub, live Supabase, deployed Render, or only planned.
- Preserve approved UI rather than gratuitously changing it.
- When debugging, inspect actual errors/state first.

User feedback that should guide future UI work:
- Opponents table became their “dream table”.
- Separate Competition/Venue controls were explicitly called “perfect”.
- Direct PNG club crest approach was confirmed working.
- New Managers page/filter replication was welcomed enthusiastically.

---

## 17. IMPORTANT DATA/PRODUCT HISTORY TO RETAIN

Substitutions Gold: 5,112 rows. Historical parsing rules include GK first, bracketed name generally subbed on unless sent off/red-card notation, 46' as half-time, stoppage-time handling, and special edge cases already resolved. Do not rebuild this layer.

Player identity correction: Mateo Joseph Fernández → canonical `Mateo Joseph`; totals 73 apps (16 starts, 57 sub apps).

Captains audit corrections included 29 Mar 1937 Jack Milburn and 24 Jan 1976 Billy Bremner.

Historical Opposition Managers identity/authority work contains many disambiguations and must remain protected. Jock Rutherford vs Tom Mather was resolved with Rutherford taking the Leeds game in question based on the 1923 sequence.

Product-derived ideas already requested include player ages/appearance number in Match Centre, milestones, manager milestones, subbed-off counts, partnerships, manager/player/opponent leaderboards, first/last appearance duration, and interconnected profile pages.

---

## 18. CURRENT FILE / CODE LANDMARKS

Frontend active files include:
- `frontend/src/App.tsx`
- `frontend/src/Leaderboard.tsx`
- `frontend/src/Managers.tsx`
- `frontend/src/ManagerIcon.tsx`
- `frontend/src/index.css`
- `frontend/src/supabase.ts`
- `frontend/public/managers/` — uploaded manager icons
- `frontend/public/flags/` — uploaded nationality flags

Relevant documentation already in `docs/` includes:
- `DATABASE_LOAD_V1.md`
- `DATA_RULES.md`
- `HISTORICAL_VALIDATION_PACK_2026-08-31.md`
- `OPPOSITION_MANAGERS_GOLD_AUDIT_2026-09-01.md`
- `REPOSITORY_STATE_2026-09-01.md`
- `SCHEMA_AUDIT_2026-08-31.md`
- `SUBSTITUTIONS_GOLD_SIGNOFF_2026-09-01.md`
- Leeds Managers audit exists on its research branch.

---

## 19. NEXT CHAT — REQUIRED STARTUP PROCEDURE

A new ChatGPT inheriting this project should do the following before making changes:

1. Read **this handover** in full.
2. Read any newer handover notes in the repo and treat them cumulatively.
3. Inspect current `main` and `ui-bolt-opponents-v1` branch state; do not assume the commit IDs above remain heads.
4. Inspect live Supabase state for any task that depends on database truth.
5. Preserve Gold/protected layers.
6. Continue from the exact unfinished point rather than rebuilding previous work.

### Exact immediate continuation as of this handover

**Continue manager icon + nationality flag integration.** Manager icons are already connected. The user states `Managers.csv` has the authoritative `Declared Nation` column. Locate that CSV, validate canonical manager mapping, populate `managers.declared_nation`, connect uploaded flags, then validate the Managers page visually/data-wise. Do not guess nationality values.

---

## 20. HANDOVER CONTINUITY RULE

This handover is intentionally comprehensive because the current ChatGPT conversation reached its maximum practical length. Future ChatGPT sessions must not reduce this to a short summary that drops historical decisions.

When the next handover is created:
- preserve all still-relevant Golden Rules;
- preserve protected/Gold layer status;
- preserve branch/repo discipline;
- preserve key forensic decisions;
- preserve current UI design rules and user-approved states;
- append all work completed after 2 September 2026;
- identify the exact unfinished next action;
- clearly distinguish Gold, live-but-not-Gold, UI-only, and planned work.

**Never allow a handover to silently erase project knowledge.**
