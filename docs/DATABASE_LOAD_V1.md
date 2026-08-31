# Database Load V1

This phase turns the validated normalized CSV build into a queryable PostgreSQL/Supabase database without changing the immutable source exports.

## Safety model

1. Run `scripts/validate_source.py` against the four source CSVs.
2. Run `scripts/build_normalized_import.py` to create deterministic relational CSVs under `build/normalized/`.
3. Apply `supabase/migrations/0001_initial_schema.sql` to an empty development database.
4. Load normalized tables with `scripts/load_postgres.py`.
5. Apply `supabase/queries/football_views.sql`.
6. Run `scripts/validate_postgres.py`; it must finish with `DATABASE LOAD V1 VALIDATION PASSED`.
7. Use `supabase/queries/post_load_validation.sql` for human-readable spot checks/audit output.
8. Do not promote the database until all integrity gates pass.

`--replace` is deliberately opt-in and is for disposable/development databases only. Production historical data must never be destructively replaced without an explicit reviewed migration. The loader runs in one transaction, rolls back on failure, and resets PostgreSQL identity sequences after explicit historical IDs are loaded so future Admin UI inserts do not collide with imported IDs.

## First analytical surfaces

- `v_player_career_totals`: appearances, starts, substitute appearances and goals.
- `v_player_opponent_totals`: appearances, starts and goals against every opponent faced.
- `v_manager_player_totals`: player usage under each manager, combining separate spells under the same manager identity.
- `v_teammate_partnerships`: appearances, starts and wins together for every player pair.
- `v_match_player_context`: Match Centre context including exact age, chronological Leeds appearance number, start/sub number, captaincy number, goals-to-date and milestone flags.

These are derived views. They never replace the atomic source-of-truth rows.

## Match Centre context and milestones

`v_match_player_context` calculates a player's age on the match date only where a full exact DOB is known. Partial/year-only birth dates deliberately return no exact age rather than inventing a date.

`appearance_number` is calculated by ordering that player's `player_matches` by `(match_date, match_id)`. The stable Match ID is the deterministic tie-breaker for the two known historical dates on which Leeds have multiple recorded matches.

The view also derives:

- Leeds debut and final appearance
- 10th, 50th, 100th, 250th and 500th appearance milestones
- start-number milestones
- first captaincy plus 10th, 50th, 100th and 250th captaincy milestones
- first Leeds goal plus 10th, 25th, 50th and 100th goal milestones
- goals scored in that match and career goals immediately after the match

This enables UI text such as `Billy Bremner — 24y 5m 20d — 312th Leeds appearance` and contextual badges such as `100th appearance`, `Leeds debut` or `50th Leeds goal` without manually maintaining those counters.

## Current snapshot gates

The audited 2026-08-31 snapshot expects 4,856 matches, 902 players, 57 manager spells, 7,282 goals and 58,527 player appearances (53,416 starts + 5,111 substitute appearances). The executable validator also protects the Ellson, Becchio, Hankin, same-date-match and Paul Robinson identity regressions, plus verifies that the career-total and Match Centre views cover the expected player/appearance populations.
