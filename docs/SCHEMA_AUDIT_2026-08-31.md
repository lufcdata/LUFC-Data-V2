# LUFC Data V2 — Schema & Migration Audit v1

**Date:** 31 August 2026  
**Source snapshots:** `MATCHES.csv`, `PLAYERS.csv`, `MANAGERS.csv`, `GOALS NEW.csv`  
**Rule:** source files remain untouched; fixes and normalisation are explicit migration rules.

## Audited totals

| Dataset | Rows | Columns | Identity finding |
|---|---:|---:|---|
| Matches | 4,856 | 66 | `Match ID` complete and unique |
| Players | 902 | 35 | `PLAYER ID` complete and unique |
| Managers | 57 | 26 | source rows represent manager/spell records |
| Goals | 7,282 | 28 | 7,281 populated Match IDs; all resolve to Matches |

Matches reconstructs **58,527 player appearances**: **53,416 starts** and **5,111 substitute appearances**. All source lineup/substitute names resolve to a Players identity using known name fields; the two Paul Robinsons must remain identity-aware.

## Identity rules

- Preserve `Match ID`; never use match date as a unique key.
- Preserve Players `PLAYER ID` as a unique legacy identity; relationships use IDs, not names.
- Generate a V2 `goal_id`; Goals `#` is not unique in the newest records.
- Separate manager people from manager spells. Do not use Managers `#` as a key.
- `Player 1`–`Player 11` are starts. `Sub 1`–`Sub 6` are substitutes used and count as appearances.

## Same-date match regression cases

The model must support multiple matches on one date:

- **1920-09-11:** Match 5 Boothtown (H, FA Cup); Match 6 Leicester City (A, Division Two)
- **1920-09-25:** Match 8 Leeds Steelworks (H, FA Cup); Match 9 Blackpool (A, Division Two)

## Confirmed migration corrections

1. **Merton Ellson — 1920-09-11, Leicester City:** Goals `MATCHID 5 -> 6`.
2. **Luciano Becchio — Millwall play-off:** source date `2009-05-15 -> 2009-05-14`; set `MATCHID = 4011`.
3. **Ray Hankin — Aston Villa, 1978-04-26:** Goals venue `Home -> Away`.
4. **Play-Off naming:** canonical display label is **Play-Offs**.
5. **Associate Members' Cup / Football League Trophy:** retain one competition lineage, but use the historically correct display name by era. Matches from 2007–2010 currently labelled `Associate Members Cup` should display `Football League Trophy` in V2.

All corrections are recorded in `data/corrections/migration_corrections.csv`. They must not be hidden in application code or applied by editing the source exports.

## Goal integrity

- 7,282 total rows.
- 7,281 populated Match IDs; zero populated IDs point to a nonexistent match.
- One source goal lacked a Match ID: the Becchio/Millwall row, now resolved to Match 4011 after the confirmed date correction.
- 153 goal rows have no Leeds `Player ID`; these are opponent own-goal scorer cases and must not be forced into the Leeds Players table.
- Goal minutes include historical non-numeric forms such as `2HF`; retain `minute_raw` and only populate a normalised minute where defensible.

## Manager integrity

Every nonblank `Leeds Manager` in Matches resolves to Managers. Repeated people correctly represent multiple spells, including Maurice Lindley, Eddie Gray, Peter Gunby and Neil Redfearn. V2 therefore uses `managers` plus `manager_spells`.

## Recommended core schema

- `players`
- `player_aliases`
- `clubs`
- `competitions`
- `competition_names`
- `seasons`
- `matches`
- `player_matches`
- `goals`
- `managers`
- `manager_spells`
- `migration_corrections`

See `supabase/migrations/0001_initial_schema.sql` for the first implementable PostgreSQL definition.

## Preservation / validation policy

- Raw source snapshots are immutable.
- Stage first; transform into normalised tables separately.
- Corrections are documented and testable.
- Derived totals are calculated from atomic rows.
- No fixture-specific application hacks.
- Before production import, validate row counts, all foreign keys, same-date match cases, appearance totals, goal totals and selected historical spot checks.
