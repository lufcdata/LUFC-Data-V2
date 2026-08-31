# Historical Validation Pack — 2026-08-31

This pack validates the first LUFC Data V2 relational answers against the immutable source CSV snapshot. The normalized relational outputs below were independently reconstructed again from the raw source `MATCHES.csv` / `GOALS NEW.csv` fields for the selected checks. All compared values matched exactly.

## PASS — all-time appearance leaders

| Rank | Player | V2 appearances | Raw-source reconstruction |
|---:|---|---:|---:|
| 1 | Jack Charlton | 773 | 773 |
| 2 | Billy Bremner | 772 | 772 |
| 3 | Paul Reaney | 749 | 749 |
| 4= | Norman Hunter | 726 | 726 |
| 4= | Paul Madeley | 726 | 726 |
| 6 | Peter Lorimer | 707 | 707 |
| 7 | Eddie Gray | 579 | 579 |
| 8 | Gary Kelly | 531 | 531 |
| 9 | Johnny Giles | 527 | 527 |
| 10 | Gary Sprake | 508 | 508 |

## PASS — Chelsea opponent intelligence

Top Leeds scorers against Chelsea from the current historical snapshot:

| Player | Goals |
|---|---:|
| Peter Lorimer | 7 |
| Mick Jones | 6 |
| Arthur Hydes | 5 |
| Tom Jennings | 4 |
| Charlie Keetley | 3 |
| Chris Crowe | 3 |
| Albert Johanneson | 3 |
| Johnny Giles | 3 |
| Billy Bremner | 3 |
| Allan Clarke | 3 |

Top Leeds appearance makers against Chelsea:

| Player | Appearances |
|---|---:|
| Jack Charlton | 29 |
| Billy Bremner | 28 |
| Paul Reaney | 27 |
| Norman Hunter | 27 |
| Peter Lorimer | 27 |
| Paul Madeley | 27 |
| Johnny Giles | 23 |
| Gary Sprake | 21 |
| Gary Kelly | 19 |
| Mick Jones | 17 |

The V2 opponent joins and the independent raw-source reconstruction produced the same rankings and values.

## PASS — Marcelo Bielsa player usage

The source snapshot contains 170 Leeds matches under Marcelo Bielsa. Top appearances under Bielsa:

| Player | Appearances |
|---|---:|
| Mateusz Klich | 157 |
| Jack Harrison | 154 |
| Stuart Dallas | 142 |
| Luke Ayling | 137 |
| Kalvin Phillips | 131 |
| Gjanni Alioski | 126 |
| Liam Cooper | 118 |
| Patrick Bamford | 117 |
| Tyler Roberts | 107 |
| Pablo Hernandez | 94 |

Again, V2 and the direct raw MATCHES reconstruction matched exactly.

## PASS — teammate partnerships

Top shared Leeds appearances in the normalized relational dataset:

| Players | Appearances together |
|---|---:|
| Paul Reaney + Norman Hunter | 637 |
| Billy Bremner + Norman Hunter | 617 |
| Billy Bremner + Paul Reaney | 590 |
| Peter Lorimer + Paul Madeley | 522 |
| Jack Charlton + Billy Bremner | 520 |
| Paul Reaney + Paul Madeley | 518 |
| Paul Reaney + Peter Lorimer | 514 |
| Norman Hunter + Peter Lorimer | 502 |
| Norman Hunter + Paul Madeley | 500 |
| Norman Hunter + Johnny Giles | 492 |

These are derived only from `player_matches` self-joins; no manually stored partnership totals exist.

## PASS — Premier League records

Current Premier League appearance leaders in the snapshot:

| Player | PL appearances |
|---|---:|
| Gary Kelly | 325 |
| Ian Harte | 213 |
| Nigel Martyn | 207 |
| Lee Bowyer | 203 |
| David Wetherall | 201 |
| Lucas Radebe | 197 |
| Harry Kewell | 181 |
| Rod Wallace | 178 |
| Alan Smith | 172 |
| Gary McAllister | 151 |

Current Premier League goal leaders:

| Player | PL goals |
|---|---:|
| Mark Viduka | 59 |
| Harry Kewell | 45 |
| Rod Wallace | 42 |
| Lee Bowyer | 38 |
| Alan Smith | 38 |
| Jimmy Floyd Hasselbaink | 34 |
| Brian Deane | 32 |
| Ian Harte | 28 |
| Rodrigo | 26 |
| Gary McAllister | 24 |

## PASS — milestone/context examples

The chronological V2 relationships produce concrete milestone examples without storing manual counters:

- Archie Gray: Leeds debut vs Cardiff City on 2023-08-06, age 17 years + 147 days.
- Billy Bremner: Leeds debut vs Chelsea on 1960-01-23, age 17 years + 45 days.
- Gary Kelly: 75th Premier League appearance vs Nottingham Forest on 1995-03-22.
- Gary Kelly: 100th Premier League appearance vs Sheffield Wednesday on 1995-12-16.
- Gary Kelly: 250th Premier League appearance vs Newcastle United on 2001-12-22.
- Mark Viduka: 50th Premier League goal reached vs Middlesbrough on 2003-08-30.

## PASS — manager milestone examples

Marcelo Bielsa chronological Leeds manager context:

- 25th Leeds win: Preston North End, 2019-04-09 (44th match in charge).
- 50th match in charge: Derby County, 2019-05-11.
- 50th Leeds win: Fulham, 2020-06-27 (93rd match in charge).
- 100th match in charge: Charlton Athletic, 2020-07-22.
- 75th Leeds win: Crewe Alexandra, 2021-08-24 (143rd match in charge).
- 150th match in charge: Southampton, 2021-10-16.

## Gate result

**Historical intelligence validation: PASS for this selected pack.**

This does not replace the database post-load validation. The PostgreSQL/Supabase load must still pass the executable database assertions before Database Load V1 can be signed off. This pack proves that the normalized relational model is already reproducing meaningful football answers from the audited source snapshot.
