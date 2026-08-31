# Database Load V1

This phase turns the validated normalized CSV build into a queryable PostgreSQL/Supabase database without changing the immutable source exports.

## Safety model

1. Run `scripts/validate_source.py` against the four source CSVs.
2. Run `scripts/build_normalized_import.py` to create deterministic relational CSVs under `build/`.
3. Apply `supabase/migrations/0001_initial_schema.sql` to an empty development database.
4. Load normalized tables with `scripts/load_postgres.py`.
5. Apply `supabase/queries/football_views.sql`.
6. Run every query in `supabase/queries/post_load_validation.sql`.
7. Do not promote the database until all integrity gates pass.

`--replace` is deliberately opt-in and is for disposable/development databases only. Production historical data must never be destructively replaced without an explicit reviewed migration.

## First analytical surfaces

- `v_player_career_totals`: appearances, starts, substitute appearances and goals.
- `v_player_opponent_totals`: appearances, starts and goals against every opponent faced.
- `v_manager_player_totals`: player usage under each manager, combining separate spells under the same manager identity.
- `v_teammate_partnerships`: appearances, starts and wins together for every player pair.
- `v_match_player_context`: the basis of Match Centre context labels, including exact age where a full DOB is known and chronological Leeds appearance number.

These are derived views. They never replace the atomic source-of-truth rows.

## Match Centre age and appearance number

`v_match_player_context` calculates a player's age on the match date from the player's exact DOB. Partial/year-only birth dates deliberately return no exact age rather than inventing a date.

`appearance_number` is calculated by ordering that player's `player_matches` by `(match_date, match_id)`. The stable Match ID is the deterministic tie-breaker for the two known historical dates on which Leeds have multiple recorded matches.

This enables UI text such as `Billy Bremner — 24y 5m 20d — 312th Leeds appearance` without storing a manually maintained appearance counter.

## Current snapshot gates

The audited 2026-08-31 snapshot expects 4,856 matches, 902 players, 57 manager spells, 7,282 goals and 58,527 player appearances (53,416 starts + 5,111 substitute appearances). The validation SQL also protects the Ellson, Becchio, Hankin, same-date-match and Paul Robinson identity regressions.
