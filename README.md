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
