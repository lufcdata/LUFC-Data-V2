# SofaScore ingestion schema v1 — design only

Date: 7 September 2026  
Status: **PROPOSED / NOT DEPLOYED**

This is a design contract for a purpose-built ingestion layer. It is intentionally separate from canonical LUFC football tables and does not authorise a production migration.

## Design goals

1. Immutable raw evidence.
2. Provider IDs remain provider-namespaced.
3. Every promoted field can be traced to its source.
4. Validation and proposed diffs are inspectable before promotion.
5. Failed/incomplete runs leave canonical LUFC data untouched.
6. Backup and rollback evidence is attached to the run.
7. Re-running the same provider event is idempotent and cannot create duplicate canonical fixtures.

## Proposed tables

### `ingestion_runs`
One row per attempted fixture ingestion.

Minimum fields:
- `ingestion_run_id` UUID PK
- `provider` text (`sofascore`)
- `provider_event_id` text
- `status` text: CAPTURED / VALIDATING / BLOCKED / READY_FOR_PROMOTION / PROMOTED / ROLLED_BACK
- `importer_git_sha` text
- `started_at`, `captured_at`, `validated_at`, `promoted_at`
- `canonical_match_id` integer nullable
- `database_writes` integer default 0 until controlled promotion
- unique `(provider, provider_event_id, importer_git_sha, captured_at)` or equivalent immutable run identity

A separate unique promoted-event guard must prevent the same provider event from creating multiple canonical matches.

### `ingestion_raw_payloads`
Immutable endpoint evidence.

Minimum fields:
- `raw_payload_id` UUID PK
- `ingestion_run_id` FK
- `provider`
- `endpoint_family` (event, lineups, incidents, managers, statistics, graph, average_positions, shotmap, standings, secondary_bbc, etc.)
- `source_url`
- `captured_at`
- `sha256`
- `payload_json` JSONB nullable where licensing/storage policy permits
- `payload_path` text nullable when bytes are retained outside Postgres
- `http_status`
- `capture_status`
- unique `(ingestion_run_id, endpoint_family, sha256)`

Raw records are append-only. They are never edited to match canonical conclusions.

### `external_identity_mappings`
Provider namespace → LUFC canonical namespace.

Minimum fields:
- `external_identity_mapping_id` bigint identity PK
- `provider`
- `entity_type` (team/player/manager/match; venue/referee only when a canonical destination exists)
- `provider_id` text
- `canonical_id` bigint
- `mapping_status` (CONFIRMED / PROPOSED / REJECTED)
- `evidence_note`
- `confirmed_at`
- unique `(provider, entity_type, provider_id)` for confirmed mappings

The table must not imply that provider and canonical IDs are interchangeable.

### `ingestion_field_provenance`
Field-level source authority for proposed/promoted values.

Minimum fields:
- `field_provenance_id` bigint identity PK
- `ingestion_run_id` FK
- `domain` (fixture, lineup, goal, etc.)
- `record_key` text
- `field_name` text
- `value_json` JSONB
- `source_provider` text
- `raw_payload_id` FK nullable
- `source_url` text nullable
- `authority` (PRIMARY / SECONDARY / DERIVED)
- `validation_status`
- `resolution_note`

Example: Brighton attendance 31661 has source_provider `bbc`, authority `SECONDARY`; stadium capacity is not an attendance source.

### `ingestion_validation_results`
Machine-readable promotion gates.

Minimum fields:
- `validation_result_id` bigint identity PK
- `ingestion_run_id` FK
- `gate_name`
- `status` (PASS / VALIDATED / RESOLVED / NOT_APPLICABLE / BLOCKED)
- `details_json` JSONB
- `created_at`
- unique `(ingestion_run_id, gate_name)`

Required gates mirror `scripts/sofascore_promotion_gate.py`.

### `ingestion_staged_events`
Lossless normalised event envelope for events that do not yet have a canonical LUFC destination.

Minimum fields:
- `staged_event_id` UUID PK
- `ingestion_run_id` FK
- `provider`
- `provider_event_id` text nullable (provider shot/incident identifier where supplied)
- `event_kind` (goal, shot, substitution, card, penalty, own_goal, period, other)
- `team_side` (LEEDS / OPPONENT)
- `provider_team_id` text
- `provider_player_id` text nullable
- `provider_secondary_player_id` text nullable
- `minute_base`, `stoppage_minute`, `period`
- `sequence_index`
- `event_json` JSONB
- `canonical_destination` text nullable
- `promotion_status` (STAGED / ELIGIBLE / SCHEMA_GAP / PROMOTED)

This is not a replacement canonical football-events table. It is an ingestion/staging envelope that prevents source loss while canonical destinations are designed.

### `ingestion_proposed_changes`
Exact pre-write diff.

Minimum fields:
- `proposed_change_id` UUID PK
- `ingestion_run_id` FK
- `sequence_index`
- `target_table`
- `operation` (INSERT / UPDATE)
- `canonical_key_json` JSONB
- `before_json` JSONB nullable
- `after_json` JSONB
- `status` (PROPOSED / BLOCKED / APPROVED / APPLIED / VERIFIED / ROLLED_BACK)
- `blocker_reason` text nullable

Every controlled production write must correspond to an approved proposed-change row.

### `ingestion_backup_manifests`
Pre-import recovery evidence.

Minimum fields:
- `backup_manifest_id` UUID PK
- `ingestion_run_id` FK unique
- `backup_path`
- `sha256`
- `created_at`
- `verified_at`
- `verification_status`
- `rollback_manifest_json` JSONB
- `retention_class` (`ROLLING_14_DAY` only for routine imports)
- `expires_at`

Hard invariant: the permanent Golden Database Master is outside routine retention/deletion logic and must never be represented as an expiring rolling backup.

## Security / exposure design

These ingestion tables are operational internals, not public app data.

- Prefer a private/non-exposed schema such as `ingestion` rather than `public`.
- Do not grant `anon` or `authenticated` access.
- If implementation constraints require `public`, enable RLS before exposure and explicitly revoke public client privileges unless a narrowly defined policy is later required.
- No browser/client-side importer should receive privileged database credentials.

## Idempotency guards

Before promotion:
- provider event must not already map to a different canonical match
- target canonical match must not already represent another provider event
- proposed INSERT keys must not already exist unless the operation is explicitly an audited UPDATE
- all 20 Leeds squad provider IDs must resolve before `player_matches`/shirt-number promotion
- opposition identities must never resolve into the Leeds `players` namespace merely to satisfy a foreign key

## Brighton v Leeds acceptance target

The Brighton dry run should be able to retain all source evidence while proposing only lossless canonical changes.

Expected final pre-backup state:

`SOURCE CAPTURE: PASS`  
`RECONCILIATION: PASS`  
`IDENTITY RESOLUTION: PASS`  
`CANONICAL DIFF: PASS OR EXPLICIT SCHEMA_GAP`  
`DATABASE WRITES: 0`

Once every **required** schema gap has an approved destination, the master gate may reach:

`15/15 VALIDATION GATES PASSED`  
`BACKUP: REQUIRED`  
`ROLLBACK MANIFEST: REQUIRED`  
`PROMOTION STATUS: BLOCKED`

Only a subsequently verified pre-import backup and rollback manifest can move the run to `READY_FOR_PROMOTION`.

## Not in v1 automatic canonical promotion

- SofaScore statistical ranking as MOTM
- inferred exact tactical slots presented as source facts
- graph/momentum values with undefined semantics
- any secondary-source field without retained provenance
- any provider ID written directly into a canonical LUFC ID column

## Migration rule

Do not deploy this design directly from this document. Before implementation:
1. review table/column names against repository conventions
2. review current production grants/RLS and Data API exposure settings
3. create the migration through the current Supabase CLI migration workflow
4. inspect generated SQL
5. run database/security advisors
6. test on a non-production project or local database
7. verify the Brighton dry run against it
8. only then consider a production schema migration
