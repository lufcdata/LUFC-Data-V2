# Opposition captains — canonical contract

Date: 7 September 2026  
Status: **PROPOSED / NOT DEPLOYED**

This document closes the *design* question raised by the Brighton v Leeds dry run. It does **not** authorise a production migration or remove the canonical-diff blocker by itself.

## Production finding

The established captain destination on a Leeds match is Leeds-specific: `matches.captain_player_id` resolves into the Leeds `players` population. There is currently no approved canonical opposition-player master population and no audited destination for the opposition captain source fact.

Therefore an opposition captain must never be inserted into `players`, and a provider player ID must never be written into a Leeds captain foreign key merely to make a fixture complete.

## Authoritative population

Create one purpose-built canonical match-fact population for the **opposition captain in a Leeds match**. Working table name:

`opposition_captains`

This is deliberately a fixture-level captain population, not an opposition-player master database.

### Required identity fields

- `opposition_captain_id` — canonical row primary key, allocated by the database/promotion transaction; never copied from SofaScore.
- `match_id` — FK to canonical `matches`; exactly one opposition captain row per match where the source fact is known.
- `captain_name_raw` — required source name.
- `captain_external_identity_key` — nullable reference/key to the provider-namespaced ingestion identity record if/when that layer is deployed.

Required uniqueness:

- unique `match_id`.

Provider idempotency belongs in the ingestion/external-provenance layer, not in `opposition_captain_id`.

Do **not** add a foreign key to `players.player_id` for the opposition captain.

## Source reconciliation

A captain proposal is eligible only when:

1. the fixture side is established explicitly;
2. the source captain provider ID is present in the captain validation evidence;
3. that provider ID reconciles to exactly one player in the opposition lineup population;
4. the source name is retained;
5. provider team/player IDs remain provider-namespaced evidence and never become LUFC canonical IDs.

The captain may be identified from the source lineup, but the canonical row stores the fixture fact rather than pretending LUFC owns a complete opposition-player identity model.

## Provenance

Canonical rows must be traceable to the approved ingestion run. Minimum intended linkage:

- `ingestion_run_id` or equivalent immutable provenance reference once the private ingestion schema is deployed;
- field-level provenance for `captain_name_raw` and any external identity reference remains attributable to the source provider.

A SofaScore player ID such as Lewis Dunk's provider ID remains in ingestion/external identity evidence. It must never become `opposition_captain_id` or `players.player_id`.

## Brighton acceptance example

For **Brighton & Hove Albion 1–1 Leeds United, 5 September 2026**, the proposed opposition captain population contains exactly one row:

- match: candidate canonical `4857`
- captain: Lewis Dunk
- SofaScore provider player ID: `115365` — provenance/external identity only
- canonical opposition player ID: none / not applicable under the current model

The source provider ID must reconcile to exactly one Brighton lineup row before the proposal is accepted.

## Relationship to existing tables

- `matches.captain_player_id`: unchanged; remains the established Leeds captain relationship.
- `players`: unchanged; remains the Leeds player population and must not receive opposition players.
- `opposition_captains`: proposed fixture-level opposition captain population.
- private ingestion/external identity layer: owns provider-namespaced player identity and provenance.

This separation preserves the rule:

**ONE DEFINITION → ONE AUTHORITATIVE POPULATION → EVERY RELEVANT SURFACE.**

## Promotion invariants

Before an opposition-captain proposal can be eligible:

1. the canonical match is resolved;
2. Leeds home/away identity is resolved;
3. captain validation is PASS;
4. the opposition captain provider ID matches exactly one opposition lineup row;
5. `captain_name_raw` is non-empty;
6. no provider player ID is written to a canonical LUFC ID field;
7. no opposition player is inserted into Leeds `players`;
8. the canonical row primary key is allocated transactionally, never guessed in the dry run;
9. duplicate captain rows for the same match are blocked;
10. provenance links the row to the approved ingestion run/source evidence.

## Deployment gate

This design alone leaves Brighton's `opposition captain` schema gap **BLOCKED**.

Before deployment:

1. review naming and data types against production conventions;
2. design/approve the private ingestion provenance linkage first;
3. create a migration through the controlled Supabase migration workflow;
4. test it on the restore/non-production project;
5. run security/database advisors;
6. verify no accidental public Data API exposure;
7. run the Brighton dry run and prove Lewis Dunk reconciles exactly without entering the Leeds player namespace;
8. take and verify a fresh rolling pre-import backup before any production promotion.

The permanent Golden Database Master is never part of routine retention/deletion logic.
