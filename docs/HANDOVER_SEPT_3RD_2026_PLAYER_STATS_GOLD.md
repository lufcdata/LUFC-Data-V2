# LUFC DATA V2 — PLAYER STATS GOLD HANDOVER

**Date:** 3 September 2026  
**Repository:** `lufcdata/LUFC-Data-V2`  
**Active UI branch:** `ui-bolt-opponents-v1`  
**Supabase project:** `nztiaxnrwojraiwipwjj`  
**Status:** PLAYER STATS / PLAYER PAGE SIGNED OFF AND LOCKED BY USER

> This handover inherits `docs/HANDOVER_SEPT_2ND_2026.md` and all work completed after it. The next ChatGPT must inspect the current GitHub branch and live Supabase state before changing anything. GitHub current branch state and live Supabase are the source of truth if they have advanced beyond this note.

---

## 1. PRIMARY CONTINUITY INSTRUCTION

Continue LUFC Data V2 from the exact current repository and Supabase state. Do not rebuild, reinterpret or casually modify protected data or signed-off UI. The governing product principle remains:

> **ONE FACT → ONE AUTHORITATIVE SOURCE → EVERY SURFACE IN SYNC.**

The UI principle remains:

> **BOLT / CURRENT SIGNED-OFF UI = VISUAL SOURCE OF TRUTH. SUPABASE = DATA SOURCE OF TRUTH.**

The Player Stats / Player Page area reached a new Golden Moment on 3 September 2026 and was explicitly signed off by the user. Treat that implementation as protected. Future work may extend it, but must not casually rewrite layout, metric definitions, mobile behaviour, player identity handling or canonical data relationships.

---

## 2. NON-NEGOTIABLE GOLDEN RULES

1. Inspect the current GitHub branch before every new repository change. Branches can advance unexpectedly.
2. Read this handover and `docs/HANDOVER_SEPT_2ND_2026.md` before meaningful work.
3. Never destroy source truth.
4. Never silently rewrite football semantics.
5. Canonical normalized Supabase tables are application truth; preserve raw/source representations where they exist.
6. Do not use names as joins when a canonical ID exists.
7. Do not invent IDs, dates, spell boundaries, metrics, ranks, honours or historical facts.
8. Validate after every meaningful data mutation.
9. User verification is mandatory before a new UI state is called Gold.
10. Do not alter Gold/protected layers merely to make a UI target fit.
11. No fixture-specific +1/-1 hacks.
12. One fact should be computed once from its authoritative source and reused across relevant surfaces.
13. Supabase 1000-row limits are an engineering constraint: paginate or aggregate server-side when a query can exceed 1000 rows.
14. Do not remove pagination from the Played Alongside pipeline.
15. Mobile Player Page styling is explicitly signed off. Do not touch it unless the user specifically asks.
16. Player Stats / Player Page is now signed off and locked. Any future change touching it must be deliberate and narrowly scoped.
17. `player_spells` is now a first-class integrity layer. Never collapse distinct Leeds spells just because they touch or overlap in the same calendar year.
18. A valid Leeds player spell does not require a competitive first-team appearance.
19. `player_spells` and `player_matches` are related but are not interchangeable: spells model club registration/playing spells; player_matches model competitive appearances.
20. Honours are not yet a proper data layer. Do not infer or fabricate them.

---

## 3. CURRENT GOLDEN MOMENT

The signed-off Player Stats implementation includes:

- universal Player Stats table for all canonical players
- clickable player rows opening the canonical Player Page
- dynamic Player Page data from Supabase
- Player Match Log
- career metrics
- competition breakdown
- opponent widgets
- appearances under Leeds managers
- played-alongside widget
- goalkeeper clean-sheet substitution for the team-results widget
- career milestones
- season log
- canonical multi-spell Leeds career display
- Player Stats filters including `+5 Apps`, `2+ Spells`, `Current`, Nationalities, competition, venue and search
- mobile Player Page polish signed off by the user

The user explicitly stated after spell integration:

> “Well done! That is signed off and locked in!”

After the `2+ Spells` filter and shorter Nationalities select were added, the user asked for this state to become a Golden Moment and be locked into GitHub.

---

## 4. REPOSITORY / GOLD RECOVERY HISTORY

Repository: `lufcdata/LUFC-Data-V2`

Primary working branch: `ui-bolt-opponents-v1`

Earlier exact Player Page recovery branch:

- `golden-player-page-2026-09-03`
- baseline commit: `115deb08a6165e239f6841417bcb1e44dcdbc111`
- meaning: earlier Billy Bremner Player Page Golden baseline before universalisation and later hero/spell improvements

Important universalisation commits:

- `79a7bc675734614f64d251c3cf14108968687b59` — universalisation baseline
- `e00dc15f5aeccd021724c67191e855e877fa0758` — Make player rows open player profiles
- `8296d79d61bb3c7e8695a96949182a6c261ad4e6` — Generalise locked player page shell
- `feb73f94bb1360304034b1446e1f8f2242563230` — Make player career metrics dynamic
- `a64640f85e67ce52735ccb34db110273589ef968` — Make player competition breakdown dynamic

Hero/mobile commits leading into this Gold state:

- `d2b9b9088e9db965b0292a8120b5d61faf0e907f` — Apply mobile player UI polish
- `0c251d3b19530ee86505ee3e201caa8420551fff` — Reduce mobile gap above born detail
- `54da9f50e7e6d3d8b8cf3709d4e4c49d8e892453` — Match player status pill reference
- `f96eb844172de29c18df5daf7544f260a7e0b61c` — Reduce desktop player status pill
- `6f8ea12c4fd0f43ce71cbdaa56109eb2f19bc403` — Make mobile player search full width
- `e703646986036034e7a35b9fd6ab21bc5b2897f6` — Use canonical player spells in profile hero
- `846c01305534d75ffd1d207451621094f8d1529c` — Add multi-spell player filter
- `615968694d28494f07d12853d290ddb74b291fc2` — Tighten player nationality filter

A new Golden recovery branch is created from the final handover commit after this file is added. Treat that branch as an immutable recovery point by project convention.

---

## 5. LIVE SUPABASE CORE STATE

Supabase project: `nztiaxnrwojraiwipwjj`

Known baseline counts inherited from the Sept 2 handover:

- matches: 4,856
- seasons: 101
- clubs: 190 total club rows
- distinct opponents in matches: 169
- players: 902
- managers: 49
- manager_spells: 57
- player_matches: 58,528
- goals: 7,282
- match_substitutions: 5,112

Protected/Gold data layers must not be rebuilt casually:

- core schema/import
- clubs/seasons
- matches
- players
- goals
- player_matches
- match core
- substitutions Gold
- match enrichments
- club reconciliation
- Opposition Managers Gold
- player identity corrections
- captain corrections
- canonical opposition-manager assignments

The Player Stats UI reads from this same live Supabase source. It does not maintain independent copies of the same football facts per screen.

---

## 6. PLAYER STATS DATA ARCHITECTURE

### Player table / leaderboard

`frontend/src/Players.tsx`

The Player Stats table uses the existing Supabase RPC:

`filtered_player_leaderboard(p_filter, p_venue)`

The returned rows provide canonical player statistics such as:

- appearances
- starts
- substitute appearances
- substituted off
- wins
- win percentage
- start percentage
- goals
- goals per game
- captain starts
- red cards
- first match
- last match
- identity/nationality/image data required for display

Player rows navigate using canonical `player_id`, not display name.

### Player Stats filters

Current filters include:

- Competition: All / League / Premier League / FA Cup / League Cup / Europe
- Venue: All / Home / Away / Neutral
- `+5 Apps`
- `2+ Spells`
- `Current`
- Nationalities
- text search

The `2+ Spells` toggle reads directly from Supabase `player_spells`, counts spell rows by canonical `player_id`, and includes a player when their spell count is at least two.

The Nationalities select has a dedicated `PlayersFilters.css` rule on desktop to reduce width and keep the filter row compact. Mobile retains full-width select behaviour.

### Player Page

`frontend/src/PlayerPage.tsx`

The selected player shell receives canonical `playerId`.

It reads:

- `players`
- `filtered_player_leaderboard`
- `player_matches`
- `matches`
- `player_spells`

and passes the selected canonical `playerId` into child components.

Current broad page order:

1. player hero
2. top 12-stat strip
3. Career Background
4. Leeds Career Metrics + Competition Breakdown
5. Most Appearances vs Clubs + Most Goals vs Clubs
6. Appearances Under Leeds Managers + Played Alongside
7. Results in Appearances for non-GKs OR Most Clean Sheets vs Clubs for GKs
8. Career Milestones
9. Season Log
10. Player Match Log rendered after PlayerPage in App

Do not casually reorder this structure.

---

## 7. PLAYER SPELLS — FIRST-CLASS INTEGRITY LAYER

Source uploaded by user:

`Leeds Players Active Years.csv`

Source shape:

- 902 rows
- columns: `Leeds Player`, `Active Years`

Canonical identity audit before import:

- CSV rows: 902
- canonical ID matches: 902
- exact display-name matches: 902
- mismatches: 0

The import was linked by the protected legacy-player ordering to canonical `player_id`; it was not name-joined.

### `public.player_spells`

Schema contains:

- `player_spell_id`
- `player_id` FK to `players`
- `spell_sequence`
- `start_year`
- `end_year`
- `is_current`
- `source_active_years`
- `source_spell_text`
- `source_name`
- `provenance_note`
- `created_at`

Constraints protect sequence uniqueness and current/end-year consistency.

Final imported layer:

- 943 spell rows
- 902 players represented
- 26 current/open spells at import time
- unique `(player_id, spell_sequence)`

### Parsing rules

The source contains several legitimate formats:

- `1920 - 1925`
- `1928 - 1939 & 1940 - 1946`
- `2011 - 2015, 2024 - present`
- `1934`
- `2011 - 12`
- `2026 - present`

The parser supports ampersand or comma spell separators, single years, `present`, full four-digit ends and abbreviated two-digit end years.

Do not automatically merge adjacent/overlapping segments. Examples such as a loan spell followed by a permanent spell can legitimately touch in the same calendar year.

### Core integrity rule

> **A player’s Leeds career is not necessarily one continuous period. All distinct Leeds playing spells must be preserved and displayed independently.**

Another locked rule established by the user:

> **A valid Leeds player spell does not require a competitive first-team appearance.**

Confirmed genuine zero-appearance spell examples:

- Tony Warner — 2010
- Jonny Howson — 2025–present
- Alex Cairns — 2024–present

These must remain in `player_spells` even though `player_matches` has no competitive first-team appearance for those spells.

Historical wartime/non-appearance examples such as Jack Milburn and George Milburn must not be deleted merely for lacking competitive appearance evidence in that spell.

---

## 8. PLAYER SPELL AUDIT AND CORRECTIONS

After import, `player_matches` + `matches.match_date` were used to audit whether any official appearance fell outside declared spell years.

Initial result after importing the actual uploaded CSV:

- 74 official appearances outside declared spell years
- 12 players affected, plus Lee Chapman requiring separate user-authoritative correction

Normalized boundaries were adjusted only where canonical appearances proved the source year range did not encompass an official appearance. Original source text was preserved with provenance.

Reconciled examples:

- Jimmy Allan: source 1925–1927, official 1928 appearance → normalized through 1928
- Bobby Abel: source 1934, official 1935 appearance → normalized through 1935
- Bobby Forrest: source 1952–1957, official 1958 appearances → normalized through 1958
- Tony Brown: source 1983–1984, official 1985 appearance → normalized through 1985
- Simon Grayson: source 1988–1992, official 1987 appearances → normalized from 1987
- Tony Agana: source 1991, official 1992 appearances → normalized through 1992
- Dominic Matteo: source 2000–2003, official 2004 appearances → normalized through 2004
- Seth Johnson: source 2001–2004, official 2005 appearances → normalized through 2005
- James Milner: source 2003–2004, official 2002 appearances → normalized from 2002
- Jordan Botaka: source 2016–2017, official 2015 appearances → normalized from 2015
- Lewie Coyle: source 2016–2019, official 2015 appearance → normalized from 2015
- Mateusz Klich: source 2017–2022, official appearance on 2023-01-04 → normalized through 2023

After reconciliation:

- appearances outside spells = 0
- affected players = 0

### Lee Chapman — user-authoritative correction

The user caught and corrected their own source error after the forensic audit.

Current canonical spell representation:

- first spell: **1989–1993**
- second spell: **1996**

`player_id=452`

Spell 1 source fields now preserve the corrected authoritative value `1989 - 1993 & 1996`; provenance states canonical appearances run through 1993-05-08.

Spell 2 source fields now preserve `1996`; provenance states canonical appearances on 1996-01-13 and 1996-01-20.

Do not revert Lee Chapman to the original erroneous `1989 - 1992 & 1995` source upload.

### Representative valid multi-spell examples

- John Charles: 1949–1957 & 1962
- Peter Lorimer: 1962–1978 & 1983–1985
- John Lukic: 1978–1983 & 1990–1996
- David Batty: 1987–1993 & 1998–2004
- Brian Deane: 1993–1997 & 2004–2005
- Fabian Delph: 2007–2009 & 2012
- Danny Pugh: 2004–2006 & 2011–2014
- Sam Byram: 2012–2016 & 2023–2026
- Joe Rodon: 2023–2024 & 2024–present

---

## 9. SPELL-AWARE PLAYER PAGE HERO

Before the spell layer, the Player Page hero derived one continuous Leeds period from earliest and latest competitive appearance. This was historically misleading for returning players; e.g. David Batty appeared as one continuous 1987–2004 period.

Current signed-off implementation queries:

`player_spells`

by selected canonical `player_id`, ordered by `spell_sequence`.

Formatting rules:

- current/open spell: `2025–present`
- single-year spell: `1996`
- normal range: `1987–1993`
- multiple spells: joined visually with ` · `

Examples in the signed-off UI:

- David Batty: `1987–1993 · 1998–2004`
- Lee Chapman: `1989–1993 · 1996`
- John Charles: `1949–1957 · 1962`
- Jonny Howson: `2006–2012 · 2025–present`

The old earliest→latest appearance range remains only as a defensive fallback if no `player_spells` rows are returned. `player_spells` is the primary truth for Leeds career periods.

Do not regress to a continuous earliest/latest career display.

---

## 10. PLAYER PAGE HERO / MOBILE SIGN-OFF

The current hero was iterated heavily against user screenshots and is now part of the signed-off Player Page.

Current hero structure includes:

- player portrait
- overlapping legacy player number badge
- display name
- full name
- position detail
- position-group label
- nationality flag/name
- Born detail using calendar icon
- Leeds United career/spells detail using `/Leeds.png`
- Status detail

Important styling lessons:

- An old `.player-profile-hero` grid in `PlayerPage.css` previously collided with the new hero layout. `PlayerPageHero.css` explicitly resets the hero layout to the intended structure.
- Huge portrait/text treatments were rejected.
- Desktop should remain compact and left-aligned.
- Mobile is centered.
- Leeds logo must not have a square container around it.
- Status pill uses outline treatment and has separate desktop/tablet/mobile sizing.

User explicitly said:

> “Okay perfect on mobile now. Don't touch that.”

Therefore do not touch mobile Player Page styling unless explicitly asked.

`frontend/src/MobilePolish.css` also includes compact mobile Player table filter styling and full-width mobile search.

---

## 11. PLAYER CAREER METRICS

`frontend/src/PlayerCareerMetrics.tsx`

Dynamic metrics from Supabase:

- Seasons
- Appearances
- Starts
- Subbed On
- Subbed Off
- Goals Scored
- Games Won
- Win Rate
- Starts as Captain
- Goals Per Game
- Red Cards

GK profiles additionally receive clean-sheet metrics.

Billy Bremner's historically verified ranks remain protected overrides because the generic leaderboard rank for GPG does not exactly reproduce the signed-off historical rank.

Billy Golden ranks:

- Seasons 4th
- Appearances 2nd
- Starts 2nd
- Subbed On 407th
- Subbed Off 160th
- Goals 5th
- Games Won 1st
- Win Rate 117th
- Starts as Captain 1st
- Goals Per Game 206th
- Red Cards 6th

Do not silently replace Billy's 206th GPG rank with a naïve generic rank calculation.

Seasons value is dynamic from distinct Leeds seasons with an appearance. A safe all-player server-side Seasons-rank helper was considered but not applied because the migration safety layer blocked it. Do not circumvent that block merely to fill the rank.

---

## 12. PLAYER PAGE TOP STAT STRIP / HONOURS

Billy Bremner signed-off values include:

- Seasons 18
- Apps 772
- Starts 771
- Subbed On 1
- Subbed Off 10
- Goals 115
- GPG 0.15
- Wins 406
- Win % 52.6%
- Starts as Captain 489
- Red Cards 3
- Honours Won 8

`Honours Won` is the deliberate exception to full dynamic sourcing at present. It remains a verified placeholder mapping for Billy (`276: 8`) while the user plans a proper honours data-improvement round later.

Do not infer honours for other players. They should remain `—` unless a proper authoritative honours layer is introduced and approved.

---

## 13. PLAYER COMPETITION BREAKDOWN

`frontend/src/PlayerCompetitionBreakdown.tsx`

Accepts canonical `playerId` and reads canonical player/match/goal/competition data. Goals exclude own goals.

Aggregates per competition:

- appearances
- goals
- wins
- win percentage

Billy was validated against the database during universalisation.

---

## 14. PLAYER MATCH LOG — SIGNED-OFF PIPELINE

`frontend/src/PlayerMatchLog.tsx`

Canonical sources include:

- `player_matches`
- `players`
- `matches`
- `goals`
- protected `match_substitutions`
- clubs
- seasons
- competitions
- `player_red_cards`

Rules:

- career appearance numbers are chronological ascending
- display order is newest first
- match-day age only shown when exact DOB is available
- goals exclude own goals
- captain from `matches.captain_player_id`
- substitutions use protected substitution data
- critical lookup: `subMap.get(m.match_id)`

Columns:

- App #
- Date
- Season
- Competition
- Opponent
- Venue
- Score
- Result
- Role
- G
- C
- RC
- Sub
- Age

Filters/toggles:

- Competition
- Venue
- Opponent
- 100/page
- Scored
- Assisted
- Captained
- Subbed On
- Sent Off

Assist coverage before 1989-08-19 is unavailable and accepted. Do not manufacture assist data.

Icons:

- `/appicons/Goal2.png`
- `/appicons/Captain%20Icon3.png`
- `/appicons/Red%20Card%20Icon2.png`

---

## 15. PLAYER SEASON LOG

`frontend/src/PlayerSeasonLog.tsx`

Dynamic by player and competition.

Uses protected substitution data. Goals exclude own goals. Assists have known historical coverage limits; wholly unavailable historical periods display `—` rather than an invented zero.

Totals recompute dynamically.

Known minor technical debt: `competitionNameMap` is constructed but render currently uses `competitions.canonical_name`. Do not casually change signed-off behaviour solely for cleanup.

---

## 16. PLAYED ALONGSIDE / 1000-ROW RULE

`frontend/src/PlayerPlayedAlongsideWidget.tsx`

This component explicitly paginates teammate appearance rows in 1000-row pages. This is required because player teammate rows can exceed Supabase's default row return limit.

Example from Billy Bremner audit:

- Billy teammate rows: 7,993
- distinct teammates: 91
- Billy + Jack Charlton shared appearances: 520

Correct Billy top teammates:

- Norman Hunter 617
- Paul Reaney 590
- Jack Charlton 520
- Paul Madeley 480
- Peter Lorimer 479

Never remove this pagination or fetch only the first 1000 rows.

General rule: any query capable of returning >1000 rows must paginate or aggregate server-side.

---

## 17. GOALKEEPER BEHAVIOUR

Exactly 78 player profiles have position group GK, confirmed by the user.

For GKs:

- PlayerCareerMetrics adds clean-sheet metrics
- `PlayerGoalkeeperCleanSheetsWidget` replaces the normal Results in Appearances block with Most Clean Sheets vs Clubs

Clean-sheet definition:

> goalkeeper appeared in the match AND Leeds opponent_score = 0

Gary Sprake is canonical `player_id=299` — not stale ID 346.

Audit reference:

- Gary Sprake: 508 apps, 216 team clean sheets

Do not use the stale 346 ID.

---

## 18. REPRESENTATIVE PLAYER AUDITS

Canonical read-only checks used during universalisation:

### Jack Charlton — `player_id=239`

- DF
- 20 seasons
- 773 apps
- 773 starts
- 0 sub apps
- 12 subbed off
- 95 goals
- W383 D190 L200
- captain 77
- reds 1
- win rate 49.5%

User explicitly visually verified Jack Charlton's universal Player Page as correct.

### Billy Bremner — `player_id=276`

- MF
- 18 seasons
- 772 apps
- 771 starts
- 1 sub app
- 10 subbed off
- 115 goals
- W406 D208 L158
- captain 489
- reds 3
- win rate 52.6%

Billy was the primary original visual/metric Golden reference.

### Gary Sprake — `player_id=299`

- GK
- 13 seasons
- 508 apps
- 506 starts
- 2 sub apps
- 3 subbed off
- 0 goals
- W286 D137 L85
- reds 1
- win rate 56.3%

### Mateo Joseph — `player_id=859`

- FW
- 3 seasons
- 73 apps
- 16 starts
- 57 sub apps
- 11 subbed off
- 6 goals
- W40 D16 L17
- win rate 54.8%

Canonical identity is `Mateo Joseph`.

### Michael Zetterer — `player_id=902`

- Current GK
- zero competitive Leeds appearances at the audit point

The user explicitly confirmed this zero-appearance state is correct because he had just joined.

All-player integrity audit during universalisation:

- leaderboard rows: 902
- max apps: 773 Jack Charlton
- duplicate player-match pairs: 0
- orphan player_matches: 0
- rows both starter and substitute: 0
- no missing player image/name/legacy ID/position group in the audited leaderboard data

---

## 19. PLAYER IDENTITY / PROFILE BACKFILL

A 902-row Players CSV enrichment added:

- `date_joined_or_turned_pro_raw`
- `date_joined_precision`
- `senior_career_clubs`

All 902 mapped by protected legacy ID.

Date precision distribution at import:

- 768 month-only dates
- 134 exact dates

Do not conflate these profile enrichments with protected appearance identity joins.

---

## 20. IMPORTANT HISTORICAL DATA PROTECTIONS

Preserve previously established corrections and Gold work, including:

- Mateo Joseph Fernández canonicalised to `Mateo Joseph`
- captain correction: 29 Mar 1937 Jack Milburn
- captain correction: 24 Jan 1976 Billy Bremner
- opposition manager Gold assignments
- Jock Rutherford/Tom Mather resolution: Jock Rutherford took the relevant Leeds game based on his final five 1922/23 games plus first six 1923/24 games
- substitutions Gold: 5,112 rows
- protected substitution timing/edge cases
- Leeds/opposition manager disambiguations from prior handovers

Do not reopen these merely because a UI query appears unexpected.

---

## 21. SOURCE-SYNC PRINCIPLE FOR PLAYER STATS

The Player Stats area is Supabase-backed and relational rather than maintaining duplicated static numbers in the frontend.

The same canonical entities drive relevant screens. For example, player identity and appearances are linked by canonical `player_id`; goals come from the canonical goals layer; substitutions come from the protected substitutions layer; spell periods come from `player_spells`.

Deliberate exceptions/coverage notes:

- Honours: not yet fully modelled; Billy's verified 8 remains a placeholder mapping
- historical assists: unavailable before established coverage; UI should show unavailable rather than inventing data
- some rank calculations retain verified Billy overrides where the generic ranking route does not reproduce the signed-off historical rank

Do not describe these as bugs; they are explicit known boundaries.

---

## 22. RECENT PLAYER STATS FILTER CHANGE

The final signed-off Player Stats filter addition before this handover:

- new `2+ Spells` toggle placed immediately beside `+5 Apps`
- uses `player_spells` grouped in the frontend by canonical `player_id`
- shows players with at least two spell rows
- composes with all existing filters
- Nationalities dropdown reduced on desktop to keep filter row compact
- mobile Nationalities select remains full width

Files:

- `frontend/src/Players.tsx`
- `frontend/src/PlayersFilters.css`

Do not replace this with name-based matching or a hard-coded list of multi-spell players.

---

## 23. CURRENT CSS / UI DISCIPLINE

Relevant files include:

- `frontend/src/index.css`
- `frontend/src/MobilePolish.css`
- `frontend/src/PlayerPage.css`
- `frontend/src/PlayerPageHero.css`
- `frontend/src/PlayerCareerMetrics.css`
- `frontend/src/PlayerMatchLog.css`
- `frontend/src/PlayersFilters.css`

Before any CSS change, fetch the current exact file from the active branch. Do not rely on copied snippets from this handover because the branch may have advanced.

Do not globally alter `.manager-status-pill`, `.lb-filter-select`, `.lb-five-toggle` or similar shared classes without checking every surface that uses them. Use scoped classes when a change is intended only for Player Stats.

The shorter Nationalities select was deliberately implemented with a player-specific class rather than globally shrinking all filter selects.

---

## 24. GITHUB WORKFLOW / SAFETY

Before every repository write:

1. inspect `ui-bolt-opponents-v1` current HEAD
2. fetch the current target file and blob SHA
3. make the smallest necessary change
4. write with the current blob SHA
5. refetch and verify syntax/content after full-file replacement
6. check final closing braces / JSX structure
7. do not assume deployment means compilation succeeded

A prior full-file replacement accidentally dropped the final `}` from `PlayerPage.tsx`. The intended changes were present in GitHub but did not appear live because the file could not compile. Restoring the closing brace fixed deployment. Always verify the file ending after full-file replacements.

GitHub Actions `.github/workflows/validate.yml` exists, but previous commits did not always have associated workflow runs. Never claim CI passed unless a fresh run/status has actually been checked.

---

## 25. GOLD / RECOVERY BRANCH RULE

The new Player Stats Golden recovery branch created after this handover should be treated as immutable by project convention.

Do not commit normal development work directly to a `golden-*` branch.

If later work breaks Player Stats, compare against the Golden branch rather than trying to reconstruct the UI from memory.

The connector available in ChatGPT can create the branch, but this handover does not assume repository-level GitHub branch protection has been enabled unless explicitly verified. “Locked” means project-Gold/protected by workflow convention unless GitHub protection settings are separately confirmed.

---

## 26. WHAT IS NOW SIGNED OFF

As of 3 September 2026, the user has explicitly signed off and locked:

- Player Stats table current visual/data behaviour
- Player Page overall current implementation
- canonical player navigation
- current hero treatment
- mobile Player Page treatment
- canonical spell-aware career display
- Player Match Log
- dynamic player career metrics
- dynamic competition breakdown
- opponent/manager/teammate widgets
- goalkeeper conditional widget behaviour
- career milestones
- season log
- `2+ Spells` Player Stats filter
- shorter desktop Nationalities dropdown

Do not call a future changed version Gold until the user visually verifies it again.

---

## 27. IMMEDIATE NEXT-CHAT STARTUP PROMPT

A new ChatGPT should begin with this operational stance:

> Continue LUFC Data V2 from the current `lufcdata/LUFC-Data-V2` repository. Work from the current `ui-bolt-opponents-v1` branch unless the user explicitly changes branches. Before changing anything, inspect the current branch, read `docs/HANDOVER_SEPT_2ND_2026.md` and `docs/HANDOVER_SEPT_3RD_2026_PLAYER_STATS_GOLD.md`, and inspect live Supabase state relevant to the requested task. Treat all Golden Rules, protected data layers, the signed-off Player Stats / Player Page, the canonical `player_spells` layer, mobile signoff and user-verification requirements as mandatory. Do not rebuild or casually modify signed-off Player Stats. Continue from the exact current repository state.

---

## 28. LIKELY NEXT PRODUCT WORK

The Player Stats area is complete for this phase. Future work should proceed to the user's next requested product/data area rather than continuing to polish Player Stats without a request.

Potential later work already known but not yet part of this Gold state:

- proper honours data layer and cross-player honours values
- additional player data-quality/enrichment round
- remaining Leeds Managers Gold engineering/integration
- further interconnected entity pages

Do not begin any of these automatically if the user asks for something else.

---

## 29. FINAL GOLD PRINCIPLE

The Player Stats work succeeded because the project stopped treating the Player Page as a collection of isolated UI numbers and instead made it a reusable view over canonical relational data.

The most important new integrity lesson from this phase is:

> **CLUB SPELL ≠ APPEARANCE RANGE.**

A Leeds player can leave and return. A registered spell can contain zero competitive appearances. Loan/permanent phases can touch in the same calendar year and still be meaningful separate spells. The database must preserve that history rather than flatten it for convenience.

Protect that principle everywhere this data is reused.
