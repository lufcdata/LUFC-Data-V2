#!/usr/bin/env python3
"""Independent validation for LUFC Data V2 relationship intelligence.

This validator deliberately recomputes selected partnership and milestone facts from
normalized atomic rows instead of querying the analytical views that expose them.
That gives us a second implementation to detect silent regressions.
"""
from __future__ import annotations
import argparse
import csv
from collections import defaultdict
from datetime import date
from pathlib import Path


def read_csv(path: Path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dir", type=Path, default=Path("build/normalized"))
    args = parser.parse_args()

    players = read_csv(args.build_dir / "players.csv")
    matches = read_csv(args.build_dir / "matches.csv")
    appearances = read_csv(args.build_dir / "player_matches.csv")
    goals = read_csv(args.build_dir / "goals.csv")
    managers = read_csv(args.build_dir / "managers.csv")
    spells = read_csv(args.build_dir / "manager_spells.csv")
    competitions = read_csv(args.build_dir / "competitions.csv")

    player_name = {r["player_id"]: r["display_name"] for r in players}
    match_by_id = {r["match_id"]: r for r in matches}
    competition_name = {r["competition_id"]: r["canonical_name"] for r in competitions}

    # Partnership validation: intersection of each player's independent Match ID set.
    match_sets = defaultdict(set)
    for row in appearances:
        match_sets[row["player_id"]].add(row["match_id"])
    by_name = {name: pid for pid, name in player_name.items()}
    reaney = by_name["Paul Reaney"]
    hunter = by_name["Norman Hunter"]
    together = match_sets[reaney] & match_sets[hunter]
    require(len(together) == 637, f"Reaney/Hunter partnership changed: {len(together)} != 637")

    # Chronological appearance milestones from atomic player_matches only.
    def player_matches(name: str, competition: str | None = None):
        pid = by_name[name]
        rows = [match_by_id[mid] for mid in match_sets[pid]]
        if competition:
            rows = [r for r in rows if competition_name[r["competition_id"]] == competition]
        return sorted(rows, key=lambda r: (parse_date(r["match_date"]), int(r["match_id"])))

    kelly_pl = player_matches("Gary Kelly", "Premier League")
    require(kelly_pl[74]["match_date"] == "1995-03-22", "Gary Kelly 75th PL appearance changed")
    require(kelly_pl[99]["match_date"] == "1995-12-16", "Gary Kelly 100th PL appearance changed")
    require(kelly_pl[249]["match_date"] == "2001-12-22", "Gary Kelly 250th PL appearance changed")

    # Competition goal milestone from atomic goals only.
    viduka = by_name["Mark Viduka"]
    viduka_pl_goals = sorted(
        [g for g in goals if g["leeds_player_id"] == viduka and competition_name[match_by_id[g["match_id"]]["competition_id"]] == "Premier League"],
        key=lambda g: (parse_date(match_by_id[g["match_id"]]["match_date"]), int(g["match_id"]), int(g["goal_id"])),
    )
    require(len(viduka_pl_goals) >= 50, "Mark Viduka has fewer than 50 PL goals in normalized data")
    require(match_by_id[viduka_pl_goals[49]["match_id"]]["match_date"] == "2003-08-30", "Viduka 50th PL goal changed")

    # Manager chronology across separate spells under one person identity.
    manager_by_name = {r["canonical_name"]: r["manager_id"] for r in managers}
    bielsa_id = manager_by_name["Marcelo Bielsa"]
    bielsa_spells = {r["manager_spell_id"] for r in spells if r["manager_id"] == bielsa_id}
    bielsa_matches = sorted(
        [m for m in matches if m["manager_spell_id"] in bielsa_spells],
        key=lambda m: (parse_date(m["match_date"]), int(m["match_id"])),
    )
    require(len(bielsa_matches) == 170, f"Bielsa match count changed: {len(bielsa_matches)} != 170")
    require(bielsa_matches[49]["match_date"] == "2019-05-11", "Bielsa 50th match changed")
    require(bielsa_matches[99]["match_date"] == "2020-07-22", "Bielsa 100th match changed")
    require(bielsa_matches[149]["match_date"] == "2021-10-16", "Bielsa 150th match changed")
    wins = [m for m in bielsa_matches if m["result"] == "Won"]
    require(wins[24]["match_date"] == "2019-04-09", "Bielsa 25th win changed")
    require(wins[49]["match_date"] == "2020-06-27", "Bielsa 50th win changed")
    require(wins[74]["match_date"] == "2021-08-24", "Bielsa 75th win changed")

    print("HISTORICAL INTELLIGENCE VALIDATION PASSED")
    print("Paul Reaney + Norman Hunter: 637 appearances together")
    print("Gary Kelly PL appearance milestones: 75 / 100 / 250 verified")
    print("Mark Viduka 50th PL goal: verified")
    print("Marcelo Bielsa manager match/win milestones: verified")


if __name__ == "__main__":
    main()
