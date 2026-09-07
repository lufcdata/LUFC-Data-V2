# SofaScore ingestion schema-gap decisions — 7 September 2026

Status: **DESIGN CONTRACT — NO PRODUCTION DATABASE WRITES**

This note records the canonical-routing decisions reached after inspecting the current production schema read-only. It does not create, alter or populate any production table.

## Governing rule

**RAW = preserve broadly. CANONICAL = promote narrowly.**

A source fact must never be squeezed into a legacy column or table that cannot represent its semantics without loss. Provider identifiers must never occupy LUFC canonical ID fields.

## Existing canonical surfaces that can be reused safely

### `matches`
The live table already has destinations for:
- match date
- season / opponent / competition identities
- Leeds manager spell
- H/A/N
- FT Leeds/opponent score and W/D/L
- stadium
- attendance
- referee
- kick-off
- round
- Leeds formation
- Leeds captain
- HT Leeds/opponent score
- first goal
- penalty-shootout score fields
- league position after match
- opposition-manager display fields

For the Brighton reference fixture, `motm_player_id` and `motm_name_raw` remain deliberately unpopulated by the automated SofaScore importer.

### `player_matches`
Safe for Leeds matchday participation only after provider player identities resolve to canonical LUFC player IDs. It can represent starter versus substitute population, but it does not currently represent unused-bench status separately or match-position intervals.

### `player_match_shirt_numbers`
Safe destination for Leeds match-specific shirt numbers after identity resolution.

### `match_substitutions`
Safe destination for **Leeds substitutions** after identity resolution. The existing table already supports player off/on, raw minute, base minute, stoppage minute, timing phase, timing-known state and evidence.

It is not an opposition-substitution table because both player foreign keys reference the LUFC `players` population. Opposition substitutions therefore remain source/staging facts unless a separate canonical opposition-event model is approved.

### `goals`
Safe destination for **Leeds goals** after identity resolution. It supports Leeds scorer, assist, timing, own-goal flag, type, location, body part and game-state fields.

It is not a complete all-goals event table: `leeds_player_id` and `assist_player_id` reference LUFC players. Opposition goals therefore must not be forced into it.

### Existing red-card / penalty / own-goal populations
The historical tables remain authoritative for their established definitions. They may be populated by future controlled import logic only where the incoming event matches the table's exact semantic population. No generic event should be routed into them merely because it is superficially similar.

## Confirmed schema gaps requiring purpose-built ingestion/canonical support

### 1. Structured opposition goals
Current `matches.opponent_scorers_raw` is a legacy/raw presentation field and is insufficient for the required chronological all-goals model.

Required future capability: structured opposition goal events with source identity, scorer, assist, timing, score before/after, match state, own-goal/penalty classification and linkage to rich shot data.

**Decision:** BLOCK promotion of structured opposition-goal detail until an approved canonical event destination exists. Do not flatten Luka Vušković's Brighton goal into `goals`.

### 2. Immutable ingestion provenance and runs
The live canonical schema has no purpose-built immutable run/raw-payload layer for this automation.

Required future capability includes:
- ingestion run ID
- provider
- provider event ID
- importer Git SHA
- capture timestamp
- endpoint/payload manifest
- payload SHA-256
- secondary-source URLs and field-level provenance
- validation results
- proposed canonical diff
- backup/rollback references

**Decision:** this must be a separate ingestion/provenance layer, not overloaded into canonical football tables.

### 3. External provider identity mappings
Required provider-namespaced mappings include at minimum team, player, manager and match identities; venue/referee mappings can be added when canonical entities exist.

**Decision:** SofaScore numeric IDs never occupy LUFC `match_id`, `club_id`, `player_id`, manager/person IDs or other canonical IDs.

### 4. Field-level provenance
`matches.attendance` can store 31,661, but the live row does not provide field-level source attribution.

**Decision:** BBC attendance may become the canonical value only with provenance retained in the ingestion layer. The value must never be inferred from stadium capacity.

The BBC Leeds hub is the approved discovery entry point for BBC enrichment; the actual match-page URL used for a field must be retained per run.

### 5. Opposition captain
There is no approved canonical destination in the inspected schema for opposition captaincy.

**Decision:** preserve Lewis Dunk captaincy in raw/staging provenance and block any claim that opposition captain has been canonically promoted until a destination is approved.

### 6. Exact tactical positions / intervals
SofaScore lineups provide broad match-context positions and player profile positions; average-position payloads provide coordinates. None is an explicit exact tactical-slot label such as RCB/LWB.

**Decision:** preserve source facts separately. Any exact slot inferred from formation + coordinates is DERIVED analysis and must never be represented as a SofaScore source fact.

### 7. Opposition substitutions and rich all-match incidents
The existing LUFC substitution table cannot represent opposition players because its player IDs reference the Leeds player population.

**Decision:** preserve and reconcile opposition substitutions in ingestion/staging. Do not contaminate `match_substitutions` with opposition identities.

### 8. Rich shot events
The shotmap provides source shot IDs, coordinates, situation, body part, xG, xGOT, goalmouth placement and goalkeeper identity. The current `goals` table cannot preserve this full shot object.

**Decision:** goal chronology and shot detail remain linked but distinct concepts. Provider shot IDs remain external source-event IDs. Rich shot data requires a purpose-built event/shot destination before canonical promotion.

## Brighton reference-fixture routing

For SofaScore event `16363258` (Brighton & Hove Albion 1–1 Leeds United, 5 September 2026):

- LUFC canonical match ID candidate remains `4857`; it is **not** the SofaScore event ID.
- Leeds formation: `3-5-2` — SofaScore primary, BBC cross-check agreed.
- Brighton formation: `4-2-3-1` — preserved and validated, but requires an approved opposition-formation destination if canonical storage is desired.
- attendance: `31661` — BBC secondary-source fact.
- Leeds league position after completed Matchweek 3: `9`.
- Leeds captain: Ethan Ampadu.
- Brighton captain: Lewis Dunk — source/staging fact pending canonical destination.
- Leeds goal: Jayden Bogle 15', assist Ao Tanaka — eligible for the Leeds `goals` population after all promotion gates pass.
- Brighton goal: Luka Vušković 71', assist Maxim De Cuyper — structured source fact, not eligible for the Leeds-only `goals` table.
- Leeds substitutions: 4 — eligible for `match_substitutions` after identity resolution and reconciliation.
- Brighton substitutions: 3 — source/staging facts pending an opposition/all-event destination.
- MOTM: NOT AUTOMATED.

## Promotion consequence

The current safe canonical diff is intentionally incomplete while these schema gaps remain. That is a feature, not a failure.

The importer must report `SCHEMA_GAP` / `BLOCKED` for required information without a lossless approved destination. A green source capture is never permission to discard data or invent a destination.

## Next design step

Design the purpose-built non-canonical ingestion schema first:
1. ingestion runs
2. immutable raw payload manifests
3. external provider identity mappings
4. staged fixture/team/lineup/incident/shot/statistic records
5. field-level provenance
6. validation results
7. proposed canonical diff
8. backup and rollback references

Only after that design is reviewed should a production migration be prepared. No production DDL or DML is authorised by this document.
