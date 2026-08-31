#!/usr/bin/env python3
"""Read-only source validation for LUFC Data V2.

The script never edits source CSV files. It validates identities and the core
cross-table relationships needed before import into PostgreSQL/Supabase.
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def norm(v: str | None) -> str:
    return (v or "").strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    args = parser.parse_args()

    matches = read_csv(args.data_dir / "MATCHES.csv")
    players = read_csv(args.data_dir / "PLAYERS.csv")
    managers = read_csv(args.data_dir / "MANAGERS.csv")
    goals = read_csv(args.data_dir / "GOALS NEW.csv")

    errors: list[str] = []

    match_ids = [norm(r.get("Match ID")) for r in matches]
    player_ids = [norm(r.get("PLAYER ID")) for r in players]
    if "" in match_ids or len(match_ids) != len(set(match_ids)):
        errors.append("Match ID must be complete and unique")
    if "" in player_ids or len(player_ids) != len(set(player_ids)):
        errors.append("PLAYER ID must be complete and unique")

    match_by_id = {norm(r["Match ID"]): r for r in matches}
    player_by_id = {norm(r["PLAYER ID"]): r for r in players}

    populated_goal_match_ids = [norm(g.get("MATCHID")) for g in goals if norm(g.get("MATCHID"))]
    bad_goal_match_ids = sorted({mid for mid in populated_goal_match_ids if mid not in match_by_id})
    if bad_goal_match_ids:
        errors.append(f"Goals contain unknown MATCHID values: {bad_goal_match_ids[:20]}")

    bad_goal_player_ids = sorted({norm(g.get("Player ID")) for g in goals if norm(g.get("Player ID")) and norm(g.get("Player ID")) not in player_by_id})
    if bad_goal_player_ids:
        errors.append(f"Goals contain unknown Player ID values: {bad_goal_player_ids[:20]}")

    alias_to_ids: dict[str, set[str]] = defaultdict(set)
    for p in players:
        pid = norm(p.get("PLAYER ID"))
        for field in ("Player", "Full Name", "First + Last Name"):
            name = norm(p.get(field))
            if name:
                alias_to_ids[name].add(pid)

    unresolved_appearances = []
    appearance_count = starts = subs = 0
    for m in matches:
        for i in range(1, 12):
            name = norm(m.get(f"Player {i}"))
            if name:
                appearance_count += 1
                starts += 1
                if name not in alias_to_ids:
                    unresolved_appearances.append((m["Match ID"], f"Player {i}", name))
        for i in range(1, 7):
            name = norm(m.get(f"Sub {i}"))
            if name:
                appearance_count += 1
                subs += 1
                if name not in alias_to_ids:
                    unresolved_appearances.append((m["Match ID"], f"Sub {i}", name))
    if unresolved_appearances:
        errors.append(f"Unresolved appearance names: {unresolved_appearances[:20]}")

    manager_names = {norm(m.get("Manager / Coach")) for m in managers if norm(m.get("Manager / Coach"))}
    unmatched_match_managers = sorted({norm(m.get("Leeds Manager")) for m in matches if norm(m.get("Leeds Manager")) and norm(m.get("Leeds Manager")) not in manager_names})
    if unmatched_match_managers:
        errors.append(f"Unmatched Leeds Manager names: {unmatched_match_managers}")

    by_date = defaultdict(list)
    for m in matches:
        by_date[norm(m.get("Date"))].append(m)
    duplicate_dates = {d: rows for d, rows in by_date.items() if d and len(rows) > 1}

    print(f"matches={len(matches)} players={len(players)} managers={len(managers)} goals={len(goals)}")
    print(f"appearances={appearance_count} starts={starts} subs={subs}")
    print(f"goal_rows_with_matchid={len(populated_goal_match_ids)} blank_goal_matchids={len(goals)-len(populated_goal_match_ids)}")
    print("same_date_match_groups=")
    for d, rows in sorted(duplicate_dates.items()):
        ids = ", ".join(f"{r['Match ID']}:{norm(r.get('Opponent'))}" for r in rows)
        print(f"  {d}: {ids}")

    expected_same_date = {
        "1920-09-11": {"5", "6"},
        "1920-09-25": {"8", "9"},
    }
    for d, ids in expected_same_date.items():
        actual = {norm(r.get("Match ID")) for r in duplicate_dates.get(d, [])}
        if actual != ids:
            errors.append(f"Same-date regression failed for {d}: expected {ids}, got {actual}")

    if errors:
        print("\nVALIDATION FAILED")
        for err in errors:
            print(f"- {err}")
        return 1

    print("\nVALIDATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
