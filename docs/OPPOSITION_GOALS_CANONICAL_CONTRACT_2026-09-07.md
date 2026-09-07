# Structured opposition goals — canonical contract

Date: 7 September 2026  
Status: **PROPOSED / NOT DEPLOYED**

This document closes the *design* question raised by the Brighton v Leeds dry run. It does **not** authorise a production migration or remove the canonical-diff blocker by itself.

## Production finding

The current canonical `goals` population is Leeds-scorer oriented. Its player foreign-key semantics (`leeds_player_id`, `assist_player_id`) belong to the Leeds `players` namespace. `match_centre_goals` is a view over that same population. `matches.opponent_scorers_raw` is useful legacy display text but is not a structured event population.

Therefore an ordinary opposition goal must never be inserted into `goals` merely to make a fixture complete, and an opposition player must never be inserted/resolved into Leeds `players` merely to satisfy those foreign keys.

Existing special-purpose populations such as own-goal and penalty tables do not constitute a complete ordinary opposition-goal population and must not be repurposed as one.

## Authoritative population

Create one purpose-built canonical population for **every goal credited to the opposition in a Leeds match**. Working table name:

`opposition_goals`

This is deliberately a match-event population, not an opposition-player master database.

### Required identity fields

- `opposition_goal_id` — canonical event primary key, allocated by the database/promotion transaction; never copied from SofaScore.
- `match_id` — FK to canonical `matches`.
- `sequence_in_match` — chronological goal sequence across both teams, so game state can be reconstructed without relying on source array order.
- `opposition_goal_number_in_match` — 1..N among opposition goals in that match.

Required uniqueness:

- unique `(match_id, sequence_in_match)` **within the opposition-goal population only if the sequence value represents the global match goal number and cannot collide with another opposition goal**.
- unique `(match_id, opposition_goal_number_in_match)`.

Provider idempotency belongs in the ingestion/external-provenance layer, not in the canonical primary key.

### Required scorer/assist fields

Opposition players do not currently have an approved canonical player master population. Preserve source identity without contaminating Leeds IDs:

- `scorer_name_raw` — required text.
- `assist_name_raw` — nullable text.
- `scorer_external_identity_key` — nullable reference/key to the provider-namespaced ingestion identity record if/when that layer is deployed.
- `assist_external_identity_key` — nullable equivalent.

Do **not** add a foreign key to `players.player_id` for an opposition scorer or assister.

### Required timing/state fields

- `minute_raw` — source/display minute, including stoppage notation where applicable.
- `minute_normalised` — base match minute suitable for ordering/filtering.
- `stoppage_minute` — nullable explicit added minute.
- `period` — nullable/source-normalised period.
- `is_own_goal` — boolean, default false.
- `score_leeds_after` — Leeds score after this goal.
- `score_opponent_after` — opposition score after this goal.
- `game_state_before` — derived Leeds-perspective state immediately before the goal (`Level`, `Leading +N`, `Trailing -N`) using the same semantic family as the existing Leeds goal population where applicable.

The score-after pair is authoritative for reconstructing the transition. Do not infer chronology from insertion order.

### Source football descriptors

The following may be nullable until an explicit provider-to-canonical vocabulary is approved:

- `goal_type`
- `location`
- `body_part`

Raw SofaScore values such as `right-foot`, `corner`, coordinates, `goalType`, or shot situation must not be silently translated into LUFC canonical vocabulary. They remain available in immutable raw/staged evidence.

### Provenance

Canonical rows must be traceable to the approved ingestion run. Minimum intended linkage:

- `ingestion_run_id` or equivalent immutable provenance reference once the private ingestion schema is deployed.
- field-level provenance remains in `ingestion_field_provenance` for source-specific facts.

Provider event/shot IDs remain provider-namespaced. They must never become `opposition_goal_id`.

## Brighton acceptance example

For **Brighton & Hove Albion 1–1 Leeds United, 5 September 2026**, the proposed opposition population contains exactly one row:

- match: candidate canonical `4857`
- scorer: Luka Vušković
- minute: 71
- assist: Maxim De Cuyper
- sequence in match: 2
- opposition goal number in match: 1
- own goal: false
- score after: Leeds 1, Brighton 1
- Leeds-perspective game state before: `Leading +1`

The incident remains linked to, but distinct from, the rich SofaScore shot event. Shot xG/xGOT, coordinates, goalmouth placement and goalkeeper data belong to the future rich-shot destination, not this goal row.

## Promotion invariants

Before an opposition-goal proposal can be eligible:

1. goal incidents reconcile to the final and half-time score;
2. chronological sequence is derived from period/time/added time, never source array order;
3. side attribution is explicit and proves the goal belongs to the opposition;
4. scorer raw name is retained;
5. any assist is retained when supplied;
6. score transition increments exactly the opposition side by one;
7. provider evidence remains preserved in raw/staging;
8. no opposition provider player ID is written to Leeds `players`;
9. the corresponding source goal is uniquely linked to its goal-shot event when a shot exists;
10. duplicate promotion of the same source goal is blocked by ingestion provenance/idempotency checks.

## Relationship to existing tables

- `goals`: unchanged; remains the established Leeds-goal population.
- `matches.opponent_scorers_raw`: retained for backwards compatibility/display until a separately approved migration chooses to derive/replace it. It is not authoritative structured storage.
- `leeds_own_goals_against`: do not rewrite or merge during this ingestion project. Historical semantics remain protected.
- penalty/own-goal specialist tables: remain specialist populations; any future synchronization with `opposition_goals` requires an explicit one-definition audit.
- `ingestion_staged_events`: continues to retain the lossless source envelope before canonical promotion.

## Deployment gate

This design alone leaves Brighton's `structured opposition goals` schema gap **BLOCKED**.

Before deployment:

1. review naming and data types against production conventions;
2. design the private ingestion provenance FK first or explicitly approve a safe interim linkage;
3. create a migration through the controlled Supabase migration workflow;
4. test it on the restore/non-production project;
5. run security/database advisors;
6. verify no public Data API exposure is introduced accidentally;
7. run the Brighton dry run and prove the proposed Vušković row exactly reconciles;
8. take and verify a fresh rolling pre-import backup before any production promotion.

The permanent Golden Database Master is never part of routine retention/deletion logic.
