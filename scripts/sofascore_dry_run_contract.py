#!/usr/bin/env python3
"""Pure validation helpers for read-only SofaScore ingestion dry runs.

No network or database access lives here. These helpers operate only on already
captured provider payloads and return explicit PASS / N/A / BLOCKED semantics.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

# Fail closed: every competition must be deliberately classified before a dry run
# can decide whether post-match league-position data is required.
LEAGUE_COMPETITION_NAMES = {"premier league"}
NON_LEAGUE_COMPETITION_NAMES = {"efl cup", "fa cup"}


class ContractError(RuntimeError):
    """Raised when a captured payload cannot satisfy the ingestion contract."""


def competition_name(event: dict[str, Any]) -> str:
    tournament = event.get("tournament")
    if not isinstance(tournament, dict):
        return ""
    return str(tournament.get("name") or "")


def league_position_requirement(event: dict[str, Any]) -> dict[str, str]:
    """Return whether the fixture should have a league-position lookup.

    League fixtures require a post-match standings snapshot. Explicitly classified
    cup fixtures are N/A. Missing or unknown competition names block the dry run so
    a new competition can never silently bypass the standings rule.
    """
    name = competition_name(event).strip()
    normalized = name.casefold()
    if normalized in LEAGUE_COMPETITION_NAMES:
        return {"status": "REQUIRED", "reason": f"league fixture: {name}"}
    if normalized in NON_LEAGUE_COMPETITION_NAMES:
        return {"status": "NOT_APPLICABLE", "reason": f"non-league fixture: {name}"}
    raise ContractError(f"competition is not classified: {name or '<missing>'}")


def attendance_candidate(
    sofascore_attendance: Any,
    *,
    secondary_attendance: Any = None,
    secondary_source: str | None = None,
    secondary_check_status: str | None = None,
) -> dict[str, Any]:
    """Return a source-attributed attendance candidate without inference.

    A real attendance is preferred from SofaScore or an approved secondary source.
    If attendance is absent, the distinction is deliberate: a successfully checked
    secondary source that genuinely does not publish a figure is a valid, non-blocking
    NULL; a failed, incomplete, or unperformed check remains unresolved and blocking.
    Stadium capacity or any other proxy must never be substituted for attendance.
    """
    if isinstance(sofascore_attendance, int) and sofascore_attendance > 0:
        return {"status": "SOURCE_FACT", "attendance": sofascore_attendance, "source": "sofascore"}

    if isinstance(secondary_attendance, int) and secondary_attendance > 0:
        if not secondary_source or not secondary_source.strip():
            raise ContractError("secondary attendance has no source attribution")
        return {
            "status": "SECONDARY_SOURCE_FACT",
            "attendance": secondary_attendance,
            "source": secondary_source.strip(),
        }

    check_status = secondary_check_status.strip().upper() if isinstance(secondary_check_status, str) else None
    if check_status == "NOT_PUBLISHED":
        if not secondary_source or not secondary_source.strip():
            raise ContractError("verified unpublished attendance has no source attribution")
        return {
            "status": "NOT_PUBLISHED",
            "attendance": None,
            "source": secondary_source.strip(),
            "blocking": False,
        }

    if check_status not in {None, "UNRESOLVED", "CHECK_FAILED", "NOT_CHECKED"}:
        raise ContractError(f"unknown secondary attendance check status: {secondary_check_status}")

    return {
        "status": "UNRESOLVED",
        "attendance": None,
        "source": secondary_source.strip() if isinstance(secondary_source, str) and secondary_source.strip() else None,
        "blocking": True,
    }


def validate_formation_crosscheck(
    sofascore_formation: str,
    *,
    secondary_formation: str | None = None,
    secondary_source: str | None = None,
) -> dict[str, Any]:
    """Validate a SofaScore formation against an optional secondary source.

    SofaScore remains the primary structured formation source. A conflicting
    secondary source blocks the dry run rather than silently overwriting it.
    """
    primary = sofascore_formation.strip() if isinstance(sofascore_formation, str) else ""
    if not primary:
        raise ContractError("SofaScore formation is missing")

    if secondary_formation is None:
        return {"status": "SOURCE_FACT", "formation": primary, "source": "sofascore", "crosscheck": "NOT_PROVIDED"}

    secondary = secondary_formation.strip() if isinstance(secondary_formation, str) else ""
    if not secondary:
        raise ContractError("secondary formation is empty")
    if not secondary_source or not secondary_source.strip():
        raise ContractError("secondary formation has no source attribution")
    if secondary != primary:
        raise ContractError(f"formation conflict: SofaScore={primary}, {secondary_source.strip()}={secondary}")

    return {"status": "VALIDATED", "formation": primary, "source": "sofascore", "crosscheck_source": secondary_source.strip()}


def motm_automation_policy() -> dict[str, Any]:
    """Make the deliberate MOTM exclusion machine-readable."""
    return {"status": "NOT_AUTOMATED", "canonical_field": "motm_player_id", "reason": "SofaScore statistical rankings are not broadcaster Man of the Match awards"}


def _lineup_entries(lineups: dict[str, Any], side: str) -> list[dict[str, Any]]:
    team = lineups.get(side)
    if not isinstance(team, dict):
        raise ContractError(f"lineups.{side} is missing")
    players = team.get("players")
    if not isinstance(players, list):
        raise ContractError(f"lineups.{side}.players is missing")
    return [entry for entry in players if isinstance(entry, dict)]


def _lineup_entry_summary(entry: dict[str, Any], side: str) -> dict[str, Any]:
    player = entry.get("player")
    if not isinstance(player, dict):
        raise ContractError(f"lineups.{side} contains an entry with no player object")
    provider_player_id = player.get("id")
    if not isinstance(provider_player_id, int):
        raise ContractError(f"lineups.{side} player {player.get('name') or '<unknown>'} has no numeric SofaScore player ID")
    return {"provider": "sofascore", "sofascore_player_id": provider_player_id, "name": str(player.get("name") or ""), "shirt_number": entry.get("shirtNumber"), "jersey_number": entry.get("jerseyNumber"), "match_position": entry.get("position"), "profile_position": player.get("position"), "substitute": entry.get("substitute") is True, "captain": entry.get("captain") is True}


def extract_captain(lineups: dict[str, Any], side: str) -> dict[str, Any]:
    entries = _lineup_entries(lineups, side)
    captains = [entry for entry in entries if entry.get("captain") is True]
    if len(captains) != 1:
        raise ContractError(f"lineups.{side} must contain exactly one captain; found {len(captains)}")
    captain = captains[0]
    if captain.get("substitute") is True:
        raise ContractError(f"lineups.{side} captain is marked as a substitute")
    summary = _lineup_entry_summary(captain, side); summary["substitute"] = False; summary["captain"] = True; return summary


def summarize_lineup_side(lineups: dict[str, Any], side: str) -> dict[str, Any]:
    if lineups.get("confirmed") is not True: raise ContractError("lineups are not confirmed")
    team = lineups.get(side)
    if not isinstance(team, dict): raise ContractError(f"lineups.{side} is missing")
    formation = team.get("formation")
    if not isinstance(formation, str) or not formation.strip(): raise ContractError(f"lineups.{side}.formation is missing")
    players = [_lineup_entry_summary(entry, side) for entry in _lineup_entries(lineups, side)]
    if not players: raise ContractError(f"lineups.{side} contains no players")
    provider_ids = [player["sofascore_player_id"] for player in players]
    if len(provider_ids) != len(set(provider_ids)): raise ContractError(f"lineups.{side} contains duplicate SofaScore player IDs")
    starters = [player for player in players if not player["substitute"]]; bench = [player for player in players if player["substitute"]]
    if len(starters) != 11: raise ContractError(f"lineups.{side} must contain exactly 11 starters; found {len(starters)}")
    captain = extract_captain(lineups, side)
    return {"provider": "sofascore", "side": side, "formation": formation, "starter_count": len(starters), "bench_count": len(bench), "squad_count": len(players), "captain": captain, "starters": starters, "bench": bench}


def summarize_lineups(lineups: dict[str, Any]) -> dict[str, Any]:
    return {"provider": "sofascore", "confirmed": True, "home": summarize_lineup_side(lineups, "home"), "away": summarize_lineup_side(lineups, "away"), "database_writes": 0, "canonical_lufc_ids_assigned": False}


def _incident_rows(incidents: dict[str, Any]) -> list[dict[str, Any]]:
    rows = incidents.get("incidents")
    if not isinstance(rows, list): raise ContractError("incidents.incidents is missing")
    return [row for row in rows if isinstance(row, dict)]


def _event_score(event: dict[str, Any], side: str) -> int:
    score = event.get(f"{side}Score")
    if not isinstance(score, dict): raise ContractError(f"event.{side}Score is missing")
    for key in ("current", "display", "normaltime"):
        value = score.get(key)
        if isinstance(value, int): return value
    raise ContractError(f"event.{side}Score has no numeric final score")


def _event_half_time_score(event: dict[str, Any], side: str) -> int:
    score = event.get(f"{side}Score")
    if not isinstance(score, dict) or not isinstance(score.get("period1"), int): raise ContractError(f"event.{side}Score.period1 is missing")
    return score["period1"]


def _incident_minute_key(row: dict[str, Any]) -> tuple[int, int]:
    time = row.get("time"); added_time = row.get("addedTime")
    return (time if isinstance(time, int) else 10_000, added_time if isinstance(added_time, int) and added_time != 999 else 0)


def reconcile_goals_with_scores(event: dict[str, Any], incidents: dict[str, Any]) -> dict[str, Any]:
    goals = [row for row in _incident_rows(incidents) if row.get("incidentType") == "goal"]; goals.sort(key=_incident_minute_key)
    home_score = away_score = half_home = half_away = 0; chronology = []
    for goal in goals:
        next_home = goal.get("homeScore"); next_away = goal.get("awayScore")
        if not isinstance(next_home, int) or not isinstance(next_away, int): raise ContractError("goal incident is missing numeric post-goal score")
        home_delta = next_home - home_score; away_delta = next_away - away_score
        if (home_delta, away_delta) not in {(1, 0), (0, 1)}: raise ContractError(f"goal score sequence is invalid: {home_score}-{away_score} -> {next_home}-{next_away}")
        home_score, away_score = next_home, next_away; minute, added = _incident_minute_key(goal)
        if minute <= 45: half_home, half_away = home_score, away_score
        player = goal.get("player"); chronology.append({"time": minute, "added_time": added, "is_home": goal.get("isHome"), "sofascore_player_id": player.get("id") if isinstance(player, dict) else None, "home_score": home_score, "away_score": away_score})
    expected_final = (_event_score(event, "home"), _event_score(event, "away"))
    if (home_score, away_score) != expected_final: raise ContractError(f"goal incidents end {home_score}-{away_score} but event final score is {expected_final[0]}-{expected_final[1]}")
    expected_half = (_event_half_time_score(event, "home"), _event_half_time_score(event, "away"))
    if (half_home, half_away) != expected_half: raise ContractError(f"goal incidents reconstruct HT {half_home}-{half_away} but event HT score is {expected_half[0]}-{expected_half[1]}")
    return {"status": "PASS", "goal_count": len(goals), "half_time_score": {"home": half_home, "away": half_away}, "final_score": {"home": home_score, "away": away_score}, "chronology": chronology}


def _substitution_key(row: dict[str, Any]) -> tuple[Any, ...]:
    player_in = row.get("playerIn"); player_out = row.get("playerOut")
    if not isinstance(player_in, dict) or not isinstance(player_out, dict): raise ContractError("substitution is missing playerIn/playerOut")
    player_in_id = player_in.get("id"); player_out_id = player_out.get("id")
    if not isinstance(player_in_id, int) or not isinstance(player_out_id, int): raise ContractError("substitution is missing numeric provider player IDs")
    time = row.get("time")
    if not isinstance(time, int): raise ContractError("substitution is missing numeric time")
    added_time = row.get("addedTime")
    return (row.get("isHome"), player_in_id, player_out_id, time, added_time if isinstance(added_time, int) else 0)


def reconcile_substitutions(incidents: dict[str, Any], average_positions: dict[str, Any]) -> dict[str, Any]:
    incident_subs = [row for row in _incident_rows(incidents) if row.get("incidentType") == "substitution"]
    position_subs = average_positions.get("substitutions")
    if not isinstance(position_subs, list): raise ContractError("average-positions substitutions are missing")
    position_subs = [row for row in position_subs if isinstance(row, dict)]
    incident_keys = Counter(_substitution_key(row) for row in incident_subs); position_keys = Counter(_substitution_key(row) for row in position_subs)
    if incident_keys != position_keys:
        missing = list((incident_keys - position_keys).elements()); extra = list((position_keys - incident_keys).elements())
        raise ContractError(f"substitution populations disagree: missing_from_average_positions={missing}, extra_in_average_positions={extra}")
    return {"status": "PASS", "substitution_count": sum(incident_keys.values()), "keys": [list(key) for key in sorted(incident_keys, key=str)]}


def _statistics_items(statistics: dict[str, Any], period: str = "ALL") -> list[dict[str, Any]]:
    periods = statistics.get("statistics")
    if not isinstance(periods, list): raise ContractError("statistics.statistics is missing")
    for period_row in periods:
        if not isinstance(period_row, dict) or period_row.get("period") != period: continue
        groups = period_row.get("groups")
        if not isinstance(groups, list): raise ContractError(f"statistics period {period} has no groups")
        items = []
        for group in groups:
            if isinstance(group, dict) and isinstance(group.get("statisticsItems"), list): items.extend(item for item in group["statisticsItems"] if isinstance(item, dict))
        return items
    raise ContractError(f"statistics period {period} is missing")


def statistic_values(statistics: dict[str, Any], name: str, *, period: str = "ALL") -> tuple[Any, Any]:
    matches = [item for item in _statistics_items(statistics, period) if item.get("name") == name]
    if len(matches) != 1: raise ContractError(f"statistic {name!r} in period {period} matched {len(matches)} rows")
    return matches[0].get("homeValue"), matches[0].get("awayValue")


def reconcile_yellow_cards(incidents: dict[str, Any], statistics: dict[str, Any]) -> dict[str, Any]:
    cards = [row for row in _incident_rows(incidents) if row.get("incidentType") == "card" and row.get("incidentClass") == "yellow"]
    home_incidents = sum(1 for row in cards if row.get("isHome") is True); away_incidents = sum(1 for row in cards if row.get("isHome") is False)
    home_stats, away_stats = statistic_values(statistics, "Yellow cards")
    if (home_incidents, away_incidents) != (home_stats, away_stats): raise ContractError(f"yellow-card populations disagree: incidents={home_incidents}-{away_incidents}, statistics={home_stats}-{away_stats}")
    return {"status": "PASS", "home": home_incidents, "away": away_incidents}


def reconcile_shot_population(statistics: dict[str, Any], shotmap: dict[str, Any]) -> dict[str, Any]:
    shots = shotmap.get("shotmap")
    if not isinstance(shots, list): raise ContractError("shotmap.shotmap is missing")
    shots = [shot for shot in shots if isinstance(shot, dict)]
    home_shots = sum(1 for shot in shots if shot.get("isHome") is True); away_shots = sum(1 for shot in shots if shot.get("isHome") is False)
    home_stats, away_stats = statistic_values(statistics, "Total shots")
    if (home_shots, away_shots) != (home_stats, away_stats): raise ContractError(f"shot populations disagree: shotmap={home_shots}-{away_shots}, statistics={home_stats}-{away_stats}")
    return {"status": "PASS", "home": home_shots, "away": away_shots, "total": len(shots)}


def reconcile_goal_shots(incidents: dict[str, Any], shotmap: dict[str, Any]) -> dict[str, Any]:
    goals = [row for row in _incident_rows(incidents) if row.get("incidentType") == "goal"]
    shots = shotmap.get("shotmap")
    if not isinstance(shots, list): raise ContractError("shotmap.shotmap is missing")
    goal_shots = [shot for shot in shots if isinstance(shot, dict) and shot.get("shotType") == "goal"]
    matches = []
    for goal in goals:
        player = goal.get("player"); provider_player_id = player.get("id") if isinstance(player, dict) else None; minute = goal.get("time")
        candidates = [shot for shot in goal_shots if isinstance(shot.get("player"), dict) and shot["player"].get("id") == provider_player_id and shot.get("time") == minute and shot.get("isHome") == goal.get("isHome")]
        if len(candidates) != 1: raise ContractError(f"goal at {minute} by provider player {provider_player_id} matched {len(candidates)} goal shots")
        matches.append({"goal_player_id": provider_player_id, "minute": minute, "shot_id": candidates[0].get("id")})
    if len(matches) != len(goal_shots): raise ContractError(f"goal-shot population mismatch: incidents={len(goals)}, shotmap_goals={len(goal_shots)}")
    return {"status": "PASS", "goal_count": len(matches), "matches": matches}
