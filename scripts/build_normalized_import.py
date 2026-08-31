#!/usr/bin/env python3
"""Build deterministic relational import files from immutable LUFC source CSVs.

No source file is edited. Confirmed corrections are applied from the machine-readable
correction ledger, and every relationship is validated before output is accepted.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORRECTIONS = ROOT / "data" / "corrections" / "correction_rules.json"
ALIASES = ROOT / "data" / "aliases" / "player_aliases.csv"


def norm(v: object) -> str:
    return str(v or "").strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_date(v: str | None) -> date | None:
    s = norm(v)
    if not s or s in {"-", "—", "―"}:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%Y, %H:%M:%S", "%m/%d/%Y, %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def iso(v: str | None) -> str:
    d = parse_date(v)
    return d.isoformat() if d else ""


def integer(v: str | None) -> int | None:
    s = norm(v).replace(",", "")
    return int(s) if s else None


def boolish(v: str | None) -> bool:
    return norm(v).lower() in {"1", "true", "yes", "y", "active"}


def apply_rules(table_name: str, rows: list[dict[str, str]], rules: list[dict]) -> list[dict[str, str]]:
    out = [dict(r) for r in rows]
    for rule in rules:
        if rule["source_table"] != table_name:
            continue
        matches = [
            idx for idx, row in enumerate(out)
            if all(norm(row.get(k)) == norm(v) for k, v in rule["where"].items())
        ]
        if len(matches) != 1:
            raise ValueError(f"Correction rule must match exactly one row; got {len(matches)}: {rule}")
        out[matches[0]].update({k: str(v) for k, v in rule["set"].items()})
    return out


def season_years(label: str) -> tuple[int | None, int | None]:
    nums = re.findall(r"\d{4}", label)
    return (int(nums[0]), int(nums[1])) if len(nums) >= 2 else (None, None)


def canonical_comp(source: str, match_date: date | None) -> tuple[str, str, str]:
    s = norm(source)
    if s in {"Play-Off", "Play-Offs"}:
        return "Play-Offs", "Play-Offs", "Play-Offs"
    if s in {"Associate Members Cup", "Associate Members' Cup", "Football League Trophy"}:
        display = "Football League Trophy" if match_date and match_date >= date(1992, 1, 1) else "Associate Members' Cup"
        return "EFL Trophy", display, "EFL Trophy"
    return s, s, s


def minute_normalised(raw: str) -> int | None:
    s = norm(raw)
    if not s:
        return None
    m = re.match(r"^(\d{1,3})", s)
    return int(m.group(1)) if m else None


def is_own_goal(row: dict[str, str]) -> bool:
    scorer = norm(row.get("Goal Scorer"))
    goal_type = norm(row.get("Goal Type")).lower()
    return "own goal" in goal_type or "(o.g.)" in scorer.lower() or "(0.g.)" in scorer.lower()


def build(data_dir: Path, output_dir: Path) -> dict[str, object]:
    raw_matches = read_csv(data_dir / "MATCHES.csv")
    raw_players = read_csv(data_dir / "PLAYERS.csv")
    raw_managers = read_csv(data_dir / "MANAGERS.csv")
    raw_goals = read_csv(data_dir / "GOALS NEW.csv")
    rules = json.loads(CORRECTIONS.read_text(encoding="utf-8"))
    goals_src = apply_rules("GOALS NEW.csv", raw_goals, rules)

    players = []
    alias_to_ids: dict[str, set[int]] = defaultdict(set)
    source_player_by_id: dict[int, dict[str, str]] = {}
    for p in raw_players:
        pid = integer(p.get("PLAYER ID"))
        if pid is None:
            raise ValueError("PLAYER ID is required")
        source_player_by_id[pid] = p
        dob = parse_date(p.get("DOB"))
        dob_raw = norm(p.get("DOB"))
        precision = "exact" if dob else ("year" if re.fullmatch(r"\d{4}", dob_raw) else "unknown")
        players.append({
            "player_id": pid,
            "legacy_player_id": pid,
            "display_name": norm(p.get("First + Last Name")) or norm(p.get("Player")),
            "full_name": norm(p.get("Full Name")),
            "sortable_name": norm(p.get("Player")),
            "date_of_birth": dob.isoformat() if dob else "",
            "birth_date_precision": precision,
            "place_of_birth": norm(p.get("Born")),
            "declared_nation": norm(p.get("Declared Nation")),
            "position_group": norm(p.get("Position")),
            "position_detail": norm(p.get("NEW POSITION")) or norm(p.get("POS")),
            "joined_from": norm(p.get("Joined From")),
            "transfer_type": norm(p.get("Transfer")),
            "date_joined_or_turned_pro": iso(p.get("Date Joined or Turned Pro")),
            "profile_image_url": norm(p.get("PROFILE")),
            "profile_text": norm(p.get("Player Summary")) or norm(p.get("INFO")),
            "status": norm(p.get("Status")),
            "active": str(boolish(p.get("Active"))).lower(),
        })
        for field in ("Player", "Full Name", "First + Last Name"):
            alias = norm(p.get(field))
            if alias:
                alias_to_ids[alias].add(pid)

    for alias_row in read_csv(ALIASES):
        alias_to_ids[norm(alias_row["alias"])].add(int(alias_row["legacy_player_id"]))

    player_aliases = []
    for alias, ids in sorted(alias_to_ids.items(), key=lambda item: item[0].casefold()):
        for pid in sorted(ids):
            player_aliases.append({"player_id": pid, "alias": alias, "alias_type": "source"})

    def resolve_player(name: str, match_date: date | None = None) -> int | None:
        n = norm(name)
        if not n or n == "―":
            return None
        ids = alias_to_ids.get(n, set())
        if len(ids) == 1:
            return next(iter(ids))
        if not ids:
            return None
        if match_date:
            candidates = []
            for pid in ids:
                source = source_player_by_id[pid]
                debut = parse_date(source.get("Debut Date"))
                first_year = integer(source.get("First App"))
                last_year = integer(source.get("Last App"))
                if debut and match_date < debut:
                    continue
                if first_year and match_date.year < first_year:
                    continue
                if last_year and match_date.year > last_year:
                    continue
                candidates.append(pid)
            if len(candidates) == 1:
                return candidates[0]
        raise ValueError(f"Ambiguous player alias {n!r}: {sorted(ids)}")

    manager_id_by_name: dict[str, int] = {}
    managers = []
    manager_spells = []
    spell_candidates: dict[str, list[dict[str, object]]] = defaultdict(list)
    for manager_row in raw_managers:
        name = norm(manager_row.get("Manager / Coach"))
        if not name:
            continue
        if name not in manager_id_by_name:
            manager_id_by_name[name] = len(manager_id_by_name) + 1
            managers.append({
                "manager_id": manager_id_by_name[name], "canonical_name": name,
                "full_name": norm(manager_row.get("Full Name")), "date_of_birth": iso(manager_row.get("Date of Birth")),
                "place_of_birth": norm(manager_row.get("Place of Birth")), "date_of_death": iso(manager_row.get("Date of Death")),
                "declared_nation": norm(manager_row.get("Declared Nation")), "profile_image_url": norm(manager_row.get("Profile")),
                "did_you_know": norm(manager_row.get("Did You Know?")), "awards": norm(manager_row.get("Awards")),
            })
        spell_id = integer(manager_row.get("ORDER"))
        if spell_id is None: raise ValueError(f"Manager spell missing ORDER: {name}")
        start = parse_date(manager_row.get("Date Joined")); end = parse_date(manager_row.get("Date Left"))
        manager_spells.append({"manager_spell_id": spell_id, "manager_id": manager_id_by_name[name], "legacy_manager_order": spell_id,
            "role": norm(manager_row.get("Role")), "date_joined": start.isoformat() if start else "", "date_left": end.isoformat() if end else "",
            "caretaker": str("caretaker" in norm(manager_row.get("Role")).lower() or norm(manager_row.get("#")) == "(C)").lower(),
            "status": norm(manager_row.get("Status")), "source_manager_name": name})
        spell_candidates[name].append({"id": spell_id, "start": start, "end": end})

    def resolve_manager_spell(name: str, match_date: date) -> int:
        candidates = [spell["id"] for spell in spell_candidates.get(norm(name), [])
            if (spell["start"] is None or match_date >= spell["start"]) and (spell["end"] is None or match_date <= spell["end"])]
        if len(candidates) != 1: raise ValueError(f"Expected one manager spell for {name!r} on {match_date}; got {candidates}")
        return int(candidates[0])

    season_ids: dict[str, int] = {}; club_ids: dict[str, int] = {}; competition_ids: dict[str, int] = {}; competition_name_ids: dict[tuple[str, str], int] = {}
    seasons = []; clubs = []; competitions = []; competition_names = []; matches = []; player_matches = []; seen_player_match = set()

    for match_row in raw_matches:
        match_id = integer(match_row.get("Match ID")); match_date = parse_date(match_row.get("Date"))
        if match_id is None or match_date is None: raise ValueError(f"Invalid Match ID/date: {match_row.get('Match ID')} {match_row.get('Date')}")
        season = norm(match_row.get("Season"))
        if season not in season_ids:
            season_ids[season] = len(season_ids) + 1; start_year, end_year = season_years(season)
            seasons.append({"season_id": season_ids[season], "display_name": season, "start_year": start_year or "", "end_year": end_year or ""})
        opponent = norm(match_row.get("Opponent"))
        if opponent not in club_ids:
            club_ids[opponent] = len(club_ids) + 1; clubs.append({"club_id": club_ids[opponent], "canonical_name": opponent, "display_name": opponent, "crest_url": ""})
        canonical, display, lineage = canonical_comp(match_row.get("Comp"), match_date)
        if canonical not in competition_ids:
            competition_ids[canonical] = len(competition_ids) + 1; competitions.append({"competition_id": competition_ids[canonical], "canonical_name": canonical, "lineage_name": lineage})
        competition_key = (canonical, display)
        if competition_key not in competition_name_ids:
            competition_name_ids[competition_key] = len(competition_name_ids) + 1; competition_names.append({"competition_name_id": competition_name_ids[competition_key], "competition_id": competition_ids[canonical], "display_name": display, "valid_from": "", "valid_to": ""})
        venue = norm(match_row.get("Venue"))
        if venue not in {"H", "A", "N"}: raise ValueError(f"Unknown match Venue {venue!r} for Match {match_id}")
        captain_id = resolve_player(match_row.get("Leeds Captain"), match_date) if norm(match_row.get("Leeds Captain")) else None
        matches.append({
            "match_id": match_id, "match_date": match_date.isoformat(), "season_id": season_ids[season], "opponent_id": club_ids[opponent],
            "competition_id": competition_ids[canonical], "competition_name_id": competition_name_ids[competition_key],
            "manager_spell_id": resolve_manager_spell(match_row.get("Leeds Manager"), match_date), "venue_type": venue,
            # Source F/A are Leeds-centric For/Against, not home/away scores. Presentation flips ordering for away fixtures.
            "leeds_score": integer(match_row.get("F")), "opponent_score": integer(match_row.get("A")), "result": norm(match_row.get("Result")),
            "stadium": norm(match_row.get("Stadium")), "attendance": integer(match_row.get("Attendance")) or "", "referee": norm(match_row.get("Referee")),
            "kickoff_time": norm(match_row.get("Kick-Off")), "round": norm(match_row.get("ROUND")), "formation": norm(match_row.get("Formation")),
            "captain_player_id": captain_id or "", "neutral": str(venue == "N").lower(), "match_info": norm(match_row.get("Match Info ✅")),
            "milestones_events": norm(match_row.get("Milestones & Events")), "source_comp": norm(match_row.get("Comp")), "source_opponent": opponent,
        })
        for index in range(1, 12):
            name = norm(match_row.get(f"Player {index}"))
            if not name: continue
            pid = resolve_player(name, match_date)
            if pid is None: raise ValueError(f"Unresolved starter {name!r} in Match {match_id}")
            key = (match_id, pid)
            if key in seen_player_match: raise ValueError(f"Duplicate player appearance in Match {match_id}: {name}")
            seen_player_match.add(key); player_matches.append({"match_id": match_id, "player_id": pid, "started": "true", "substitute": "false", "lineup_order": index, "source_slot": f"Player {index}"})
        for index in range(1, 7):
            name = norm(match_row.get(f"Sub {index}"))
            if not name: continue
            pid = resolve_player(name, match_date)
            if pid is None: raise ValueError(f"Unresolved substitute {name!r} in Match {match_id}")
            key = (match_id, pid)
            if key in seen_player_match: raise ValueError(f"Duplicate player appearance in Match {match_id}: {name}")
            seen_player_match.add(key); player_matches.append({"match_id": match_id, "player_id": pid, "started": "false", "substitute": "true", "lineup_order": 11 + index, "source_slot": f"Sub {index}"})

    match_by_id = {int(row["match_id"]): row for row in matches}; competition_name_by_id = {int(row["competition_id"]): row["canonical_name"] for row in competitions}
    goals = []; goal_crosscheck_failures = []
    for source_row, goal_row in enumerate(goals_src, start=2):
        legacy_number = integer(goal_row.get("#")); match_id = integer(goal_row.get("MATCHID")); goal_date = parse_date(goal_row.get("Date"))
        if legacy_number is None or match_id is None or goal_date is None: raise ValueError(f"Goal missing required identity/date after corrections: row {source_row}")
        match = match_by_id.get(match_id)
        if match is None: raise ValueError(f"Goal references missing Match ID {match_id}: row {source_row}")
        own_goal = is_own_goal(goal_row); scorer_id = integer(goal_row.get("Player ID"))
        if scorer_id is not None and scorer_id not in source_player_by_id: raise ValueError(f"Goal has unknown Player ID {scorer_id}: row {source_row}")
        if scorer_id is None and not own_goal: raise ValueError(f"Non-own goal missing Leeds Player ID: row {source_row} {goal_row.get('Goal Scorer')}")
        assist_raw = norm(goal_row.get("Assisted By")); assist_id = None
        if assist_raw and assist_raw != "―":
            assist_id = resolve_player(assist_raw, goal_date)
            if assist_id is None: raise ValueError(f"Unresolved assist {assist_raw!r}: row {source_row}")
        venue_map = {"Home": "H", "Away": "A", "Neutral": "N", "H": "H", "A": "A", "N": "N"}; goal_venue = venue_map.get(norm(goal_row.get("Venue")), norm(goal_row.get("Venue")))
        goal_canonical = canonical_comp(goal_row.get("Comp"), goal_date)[0]
        checks = {"date": goal_date.isoformat() == match["match_date"], "opponent": norm(goal_row.get("Opponent")) == match["source_opponent"],
            "competition": goal_canonical == competition_name_by_id[int(match["competition_id"])], "venue": goal_venue == match["venue_type"]}
        if not all(checks.values()): goal_crosscheck_failures.append({"source_row": source_row, "legacy_goal_number": legacy_number, "match_id": match_id, "checks": checks})
        goals.append({"goal_id": len(goals) + 1, "legacy_goal_number": legacy_number, "match_id": match_id, "leeds_player_id": scorer_id or "",
            "scorer_name_raw": norm(goal_row.get("Goal Scorer")), "minute_raw": norm(goal_row.get("Minute")), "minute_normalised": minute_normalised(goal_row.get("Minute")) or "",
            "goal_number": integer(goal_row.get("Goal #")) or "", "is_own_goal": str(own_goal).lower(), "assist_player_id": assist_id or "", "assist_name_raw": assist_raw,
            "goal_type": norm(goal_row.get("Goal Type")), "location": norm(goal_row.get("Location")), "body_part": norm(goal_row.get("Body Part")),
            "goal_state": norm(goal_row.get("Goal State")), "game_state": norm(goal_row.get("Game State")), "kit_note": norm(goal_row.get("Kit Note")), "source_row_number": source_row})
    if goal_crosscheck_failures: raise ValueError(f"Goal/match cross-check failed for {len(goal_crosscheck_failures)} rows: {goal_crosscheck_failures[:5]}")

    # Output generated files. Match-derived clubs remain stable; master catalogue extension is layered separately.
    for filename in ("seasons", "clubs", "competitions", "competition_names", "players", "player_aliases", "managers", "manager_spells", "matches", "player_matches", "goals"):
        rows = locals()[filename]
        if rows:
            write_csv(output_dir / f"{filename}.csv", list(rows[0]), rows)
    summary = {"source_counts": {"matches": len(raw_matches), "players": len(raw_players), "managers_spells": len(raw_managers), "goals": len(raw_goals)},
        "normalized_counts": {"seasons": len(seasons), "clubs": len(clubs), "competitions": len(competitions), "competition_names": len(competition_names), "players": len(players),
            "player_aliases": len(player_aliases), "managers": len(managers), "manager_spells": len(manager_spells), "matches": len(matches), "player_matches": len(player_matches), "goals": len(goals)},
        "appearances": {"total": len(player_matches), "starts": sum(1 for r in player_matches if r["started"] == "true"), "subs": sum(1 for r in player_matches if r["substitute"] == "true")},
        "own_goals": sum(1 for r in goals if r["is_own_goal"] == "true"), "correction_rules_applied": sum(1 for r in rules if r["source_table"] == "GOALS NEW.csv"), "goal_crosscheck_failures": 0}
    (output_dir / "build_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8"); return summary


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--data-dir", type=Path, required=True); parser.add_argument("--output-dir", type=Path, default=Path("build/normalized")); args = parser.parse_args()
    if args.output_dir.exists(): shutil.rmtree(args.output_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True); print(json.dumps(build(args.data_dir, args.output_dir), indent=2))

if __name__ == "__main__": main()
