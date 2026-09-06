# LUFC Data V2 — Golden Database Master

**Snapshot date:** 6 September 2026  
**Supabase project:** `nztiaxnrwojraiwipwjj`  
**Repository:** `lufcdata/LUFC-Data-V2`  
**Source branch at snapshot:** `ui-bolt-opponents-v1`  
**Source code commit:** `2886ecbe5561306bad830d01cb614ab6df454a14`  
**Golden branch:** `golden-database-2026-09-06`

## RESTORE STATUS — IMPORTANT

**This Golden branch is permanent, but the disaster-recovery payload is NOT YET complete.**

The branch currently preserves the matching source-code state plus canonical database fingerprints. It must **not** be described as a complete/restorable Golden Database Master until a verified full database dump/archive has been added to the protected backup location and a test restore has been validated.

The finished Golden Database Master must contain everything required to reconstruct the LUFC production database as it existed on 6 September 2026, including all relevant database data and database objects required by the application.

A completed Golden backup must include, as applicable:

- all LUFC production data tables and every row;
- staging/provenance/audit tables that form part of LUFC Data V2;
- schemas and table definitions;
- primary keys, foreign keys, unique constraints and check constraints;
- indexes;
- sequences / identity state;
- views and materialized views;
- PostgreSQL functions / RPCs;
- triggers;
- RLS configuration and policies;
- required extensions and other database objects;
- migration/version reference sufficient to reproduce the schema;
- a restore procedure;
- cryptographic/integrity hashes and row-count verification;
- the exact matching application Git commit.

The backup is only considered **GOLDEN RESTORABLE** after restoration into an isolated database has succeeded and verification has confirmed that the restored database matches the captured Golden state.

## PERMANENT PROTECTION RULE

**The branch `golden-database-2026-09-06` is permanent and must never be deleted, rotated, expired, renamed away, or included in any automated cleanup process.**

It is the protected Golden Database Master recovery baseline for LUFC Data V2 immediately before the SofaScore automated match-ingestion project.

## Rolling backup retention rule

Future pre-import backups are a separate backup population and are not Golden Masters.

- Create a fresh temporary backup before every production scrape + canonical database update.
- Retain each temporary rolling backup for **14 days**.
- Temporary backups older than 14 days may be deleted after verification.
- Cleanup logic must explicitly exclude `golden-database-2026-09-06` and any future resource marked as a Golden Master.
- The Golden Database Master has **no expiry date**.
- Failure to create and verify a required pre-import backup must block the production import.

## Core safety rule

**COMPLETE → CORRECT → CONSISTENT → REVERSIBLE → ONLY THEN CANONICAL**

No automated scraper may write directly to canonical tables. New match data must pass through raw capture, staging, identity resolution, completeness validation, proposed diff and transactional promotion.

## Golden-state canonical fingerprints

These fingerprints were calculated directly from the live production database on 6 September 2026 and provide an integrity reference for this Golden state.

| Table | Rows | Content hash |
|---|---:|---|
| `clubs` | 190 | `efe1be087e1d07e0173b333e4c449acf` |
| `competition_names` | 16 | `7c1dab39a101bc30143e10460c6f9027` |
| `competitions` | 16 | `70de7c2d7b269ce28c530d6c20fcb4d0` |
| `goals` | 7,282 | `358e6d9f3b6d406d07b806868b592650` |
| `leeds_manager_red_cards` | 7 | `3b8786245f018d84804c44ea5383074b` |
| `leeds_own_goals_against` | 144 | `c723b474a0f3cb8a512444881886a572` |
| `leeds_penalties` | 590 | `72ca228661af6e3a679b98ed43947292` |
| `manager_spells` | 57 | `f3a27d300311c03e3199fad741b8ae00` |
| `managerial_assignment_people` | 4,842 | `ceb6b040d320b92c2d814db99a89528a` |
| `managerial_assignments` | 4,856 | `31a2915078c01a4ab9f6c74bb5e9b9e4` |
| `managerial_people` | 883 | `9f1357f198a71693fdc0791140c719bc` |
| `managers` | 49 | `f332b0393be2a4a1009d7d73739ba103` |
| `match_substitutions` | 5,112 | `836aedd8b9bdb9a78bfc7c07e4a56969` |
| `matches` | 4,856 | `e7808bd5541a7a4f2e93bb87fa5906c8` |
| `opposition_penalties` | 519 | `69d71ed02a7077d4221c6bd947a85e3b` |
| `opposition_red_cards` | 212 | `1285e71142e0746d6eb870666503fc35` |
| `player_match_shirt_numbers` | 1,409 | `98659d3c99314142e47d987559309359` |
| `player_matches` | 58,528 | `b5d6dcb19b04f3bdad85d5ae9c1a8f2d` |
| `player_red_cards` | 179 | `1e98de94d1c60c8fbef2dc9aca98da12` |
| `player_season_squad_numbers` | 1,152 | `4eeb54ca7f9ce5f1b00e52e76f502243` |
| `players` | 904 | `f78ed34f08245ba694b0a84fa39bab8a` |
| `seasons` | 101 | `64773c33c7ec9826c4bdb7e6ed557371` |

## Completion gate

Do not mark this backup as **GOLDEN RESTORABLE** until all of the following are true:

1. A full database dump/archive has been captured from production.
2. The archive is stored in a protected location that is not publicly accessible.
3. Its checksum is recorded here.
4. A restore has been performed into an isolated target database.
5. Schema objects, row counts and canonical fingerprints have been verified against the Golden state.
6. The restore procedure is documented and proven.

Until those conditions pass, this branch remains the **permanent Golden baseline**, but not yet the completed disaster-recovery archive.