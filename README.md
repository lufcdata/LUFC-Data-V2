# LUFC Data V2

A new, isolated Leeds United historical/statistical database and website project.

## Golden rules

- This repository is the only codebase for LUFC Data V2. Existing football repositories must remain untouched.
- Source CSV exports are immutable inputs. Corrections and normalisation are explicit, documented and testable.
- Stable IDs are relationship keys. Names and dates are never unique relationship keys.
- Multiple Leeds matches on the same date are supported by design.
- Derived totals are calculated from atomic records; they are not stored as authoritative source facts.
- Historical competition names are preserved by era while sharing a stable competition lineage.
- `main` should remain deployable.
- Credentials and API keys must never be committed.

## Current audited source snapshot

- Matches: 4,856 rows
- Players: 902 rows
- Managers/spells: 57 rows
- Leeds goals: 7,282 rows
- Reconstructable player appearances: 58,527
  - Starts: 53,416
  - Substitute appearances: 5,111

## Normalized import build

`scripts/build_normalized_import.py` now converts the four immutable source CSVs into deterministic relational CSVs for the V2 schema. It applies only machine-readable confirmed corrections, resolves player aliases and manager spells, normalises mixed source dates, reconstructs starting/substitute appearances, identifies opponent own goals, and refuses to finish if any goal no longer agrees with its linked match on date, opponent, competition or venue.

Validated normalized output from the audited snapshot:

- Seasons: 101
- Clubs/opponents: 169
- Competition lineages: 16
- Players: 902
- Player aliases: 2,491
- Managers: 49 people across 57 spells
- Matches: 4,856
- Player-match appearances: 58,527
- Goals: 7,282
- Opponent own goals: 153
- Goal-to-match cross-check failures after confirmed corrections: 0

Generated files live under `build/` and are deliberately ignored by Git. Source CSVs remain outside the repository.

## Confirmed migration corrections

1. Merton Ellson, Leicester City away, 1920-09-11: Goals `MATCHID` 5 -> 6.
2. Luciano Becchio, Millwall play-off, 2009-05-14: source date 2009-05-15 -> 2009-05-14 and `MATCHID` -> 4011.
3. Ray Hankin, Aston Villa, 1978-04-26: Goals venue `Home` -> `Away`.
4. Canonical display label: `Play-Offs`.
5. Associate Members' Cup / Football League Trophy remain one competition lineage with historically correct names by era.

## Planned architecture

- PostgreSQL / Supabase for relational data
- React front end, evolving from the supplied Bolt UI
- Python import, validation and scraping utilities
- GitHub Actions for validation and later scheduled ingestion
- `lufcdata.com` as the public front end

## Core schema

`players`, `player_aliases`, `clubs`, `competitions`, `competition_names`, `seasons`, `matches`, `player_matches`, `goals`, `managers`, `manager_spells`, `migration_corrections`.

See `docs/SCHEMA_AUDIT_2026-08-31.md` and `supabase/migrations/0001_initial_schema.sql`.
