# Database Load V1

This phase turns the validated normalized CSV build into a queryable PostgreSQL/Supabase database without changing the immutable source exports.

## Safety model

1. Run `scripts/validate_source.py` against the four source CSVs.
2. Run `scripts/build_normalized_import.py` to create deterministic relational CSVs under `build/normalized/`.
3. Run `scripts/validate_historical_intelligence.py` against the normalized build. It independently reconstructs selected partnership and milestone facts from atomic rows and must finish with `HISTORICAL INTELLIGENCE VALIDATION PASSED`.
4. Apply `supabase/migrations/0001_initial_schema.sql` to an empty development database.
5. Load normalized tables with `scripts/load_postgres.py`.
6. Apply `supabase/queries/football_views.sql`.
7. Run `scripts/validate_postgres.py`; it must finish with `DATABASE LOAD V1 VALIDATION PASSED`.
8. Use `supabase/queries/post_load_validation.sql` for human-readable spot checks/audit output.
9. Do not promote the database until all integrity gates pass.

`--replace` is deliberately opt-in and is for disposable/development databases only. Production historical data must never be destructively replaced without an explicit reviewed migration. The loader runs in one transaction, rolls back on failure, and resets PostgreSQL identity sequences after explicit historical IDs are loaded so future Admin UI inserts do not collide with imported IDs.

## First analytical surfaces

- `v_player_career_totals`: appearances, starts, substitute appearances and goals.
- `v_player_opponent_totals`: appearances, starts and goals against every opponent faced.
- `v_manager_player_totals`: player usage under each manager, combining separate spells under the same manager identity.
- `v_teammate_partnerships`: appearances, starts and wins together for every player pair.
- `v_match_player_context`: Match Centre context including exact age, chronological Leeds appearance number, start/sub number, captaincy number, goals-to-date, competition-specific appearance/goal counters and milestone flags.
- `v_match_manager_context`: cumulative Leeds manager match/win context across all spells for the same manager identity, while retaining spell-specific match numbers.

These are derived views. They never replace the atomic source-of-truth rows.

## Match Centre context and milestones

`v_match_player_context` calculates a player's age on the match date only where a full exact DOB is known. Partial/year-only birth dates deliberately return no exact age rather than inventing a date.

`appearance_number` is calculated by ordering that player's `player_matches` by `(match_date, match_id)`. The stable Match ID is the deterministic tie-breaker for the two known historical dates on which Leeds have multiple recorded matches.

The view derives career milestones including Leeds debut/final appearance, appearance milestones, start milestones, captaincy milestones, first Leeds goal and career goal milestones. It also calculates competition-specific counters by `(player_id, competition_id)`, enabling generic records such as a 75th Premier League appearance, 50th Premier League goal or 25th FA Cup goal without manually stored totals.

This enables UI text such as `Billy Bremner — 24y 5m 20d — 312th Leeds appearance` and contextual badges such as `100th appearance`, `Leeds debut`, `50th Leeds goal`, `75th Premier League appearance` or `50th Premier League goal`.

## Manager milestones

`v_match_manager_context` orders matches by `(match_date, match_id)` across the manager person identity, so separate Leeds spells are combined for career-level manager records. `spell_match_number` is retained for tenure-specific presentation.

The view derives manager match milestones and cumulative Leeds win milestones. This supports records such as `100th match as Leeds manager` or `50th win at Leeds` while still allowing a UI to distinguish a manager's second or third spell.

## Teammate partnerships

`v_teammate_partnerships` is generated entirely from pairs of players who share the same `match_id`. No partnership total is manually stored.

Because this is a distinctive LUFC Data statistic with little external historical reference material, the project uses an independent second calculation as its trust gate. `scripts/validate_historical_intelligence.py` reconstructs selected partnership totals directly from each player's Match ID set rather than reading `v_teammate_partnerships`. The current protected anchor is Paul Reaney + Norman Hunter at 637 Leeds appearances together.

The same independent validator reconstructs selected competition and manager milestones from atomic rows, including Gary Kelly Premier League appearance milestones, Mark Viduka's 50th Premier League goal, and Marcelo Bielsa match/win milestones. These regression anchors are deliberately separate from the analytical views they protect.

## Current snapshot gates

The audited 2026-08-31 snapshot expects 4,856 matches, 902 players, 57 manager spells, 7,282 goals and 58,527 player appearances (53,416 starts + 5,111 substitute appearances).

The executable PostgreSQL validator protects the Ellson, Becchio, Hankin, same-date-match and Paul Robinson identity regressions; checks career and Match Centre populations; checks unique career/competition appearance numbering; validates manager context numbering; and verifies the protected partnership, player competition milestone and manager milestone examples against the real database after load.
