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
        return {
            "status": "REQUIRED",
            "reason": f"league fixture: {name}",
        }
    if normalized in NON_LEAGUE_COMPETITION_NAMES:
        return {
            "status": "NOT_APPLICABLE",
            "reason": f"non-league fixture: {name}",
        }
    raise ContractError(f"competition is not classified: {name or '<missing>'}")


def attendance_candidate(
    sofascore_attendance: Any,
    *,
    secondary_attendance: Any = None,
    secondary_source: str | None = None,
) -> dict[str, Any]:
    """Return a source-attributed attendance candidate without inference.

    SofaScore may omit attendance. An approved secondary source can supply it, but
    stadium capacity or any other proxy must never be substituted for attendance.
    """
    if isinstance(sofascore_attendance, int) and sofascore_attendance > 0:
        return {
            "status": "SOURCE_FACT",
            "attendance": sofascore_attendance,
            "source": "sofascore",
        }
    if isinstance(secondary_attendance, int) and secondary_attendance > 0:
        if not secondary_source or not secondary_source.strip():
            raise ContractError("secondary attendance has no source attribution")
        return {
            "status": "SECONDARY_SOURCE_FACT",
            "attendance": secondary_attendance,
            "source": secondary_source.strip(),
        }
    return {
        "status": "UNAVAILABLE",
        "attendance": None,
        "source": None,
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
        return {
            "status": "SOURCE_FACT",
            "formation": primary,
            "source": "sofascore",
            "crosscheck": "NOT_PROVIDED",
        }

    secondary = secondary_formation.strip() if isinstance(secondary_formation, str) else ""
    if not secondary:
        raise ContractError("secondary formation is empty")
    if not secondary_source or not secondary_source.strip():
        raise ContractError("secondary formation has no source attribution")
    if secondary != primary:
        raise ContractError(
            f"formation conflict: SofaScore={primary}, {secondary_source.strip()}={secondary}"
        )

    return {
        "status": "VALIDATED",
        "formation": primary,
        "source": "sofascore",
        "crosscheck_source": secondary_source.strip(),
    }


def motm_automation_policy() -> dict[str, Any]:
    """Make the deliberate MOTM exclusion machine-readable."""
    return {
        "status": "NOT_AUTOMATED",
        "canonical_field": "motm_player_id",
        "reason": "SofaScore statistical rankings are not broadcaster Man of the Match awards",
    }


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
        raise ContractError(
            f"lineups.{side} player {player.get('name') or '<unknown>'} has no numeric SofaScore player ID"
        )

    return {
        "provider": "sofascore",
        "sofascore_player_id": provider_player_id,
        "name": str(player.get("name") or ""),
        "shirt_number": entry.get("shirtNumber"),
        "jersey_number": entry.get("jerseyNumber"),
        # Match-context position belongs to the lineup entry. Keep it separate from
        # the nested player profile position; never silently substitute one for the other.
        "match_position": entry.get("position"),
        "profile_position": player.get("position"),
        "substitute": entry.get("substitute") is True,
        "captain": entry.get("captain") is True,
    }


def extract_captain(lineups: dict[str, Any], side: str) -> dict[str, Any]:
    """Return one source-backed starting captain for a lineup side.

    Captaincy is read from the match lineup entry itself. A captain marked as a
    substitute or zero/multiple captains blocks promotion.
    """
    entries = _lineup_entries(lineups, side)
    captains = [entry for entry in entries if entry.get("captain") is True]
    if len(captains) != 1:
        raise ContractError(
            f"lineups.{side} must contain exactly one captain; found {len(captains)}"
        )

    captain = captains[0]
    if captain.get("substitute") is True:
        raise ContractError(f"lineups.{side} captain is marked as a substitute")

    summary = _lineup_entry_summary(captain, side)
    summary["substitute"] = False
    summary["captain"] = True
    return summary


def summarize_lineup_side(lineups: dict[str, Any], side: str) -> dict[str, Any]:
    """Validate and summarize one confirmed SofaScore matchday lineup.

    This deliberately preserves provider IDs and source fields only. It does not
    assign LUFC player IDs or infer exact positions from profile metadata.
    """
    if lineups.get("confirmed") is not True:
        raise ContractError("lineups are not confirmed")

    team = lineups.get(side)
    if not isinstance(team, dict):
        raise ContractError(f"lineups.{side} is missing")

    formation = team.get("formation")
    if not isinstance(formation, str) or not formation.strip():
        raise ContractError(f"lineups.{side}.formation is missing")

    players = [_lineup_entry_summary(entry, side) for entry in _lineup_entries(lineups, side)]
    if not players:
        raise ContractError(f"lineups.{side} contains no players")

    provider_ids = [player["sofascore_player_id"] for player in players]
    if len(provider_ids) != len(set(provider_ids)):
        raise ContractError(f"lineups.{side} contains duplicate SofaScore player IDs")

    starters = [player for player in players if not player["substitute"]]
    bench = [player for player in players if player["substitute"]]
    if len(starters) != 11:
        raise ContractError(
            f"lineups.{side} must contain exactly 11 starters; found {len(starters)}"
        )

    captain = extract_captain(lineups, side)

    return {
        "provider": "sofascore",
        "side": side,
        "formation": formation,
        "starter_count": len(starters),
        "bench_count": len(bench),
        "squad_count": len(players),
        "captain": captain,
        "starters": starters,
        "bench": bench,
    }


def summarize_lineups(lineups: dict[str, Any]) -> dict[str, Any]:
    """Return the validated home/away lineup package for a read-only dry run."""
    return {
        "provider": "sofascore",
        "confirmed": True,
        "home": summarize_lineup_side(lineups, "home"),
        "away": summarize_lineup_side(lineups, "away"),
        "database_writes": 0,
        "canonical_lufc_ids_assigned": False,
    }


def _incident_rows(incidents: dict[str, Any]) -> list[dict[str, Any]]:
    rows = incidents.get("incidents")
    if not isinstance(rows, list):
        raise ContractError("incidents.incidents is missing")
    return [row for row in rows if isinstance(row, dict)]


def _event_score(event: dict[str, Any], side: str) -> int:
    score = event.get(f"{side}Score")
    if not isinstance(score, dict):
        raise ContractError(f"event.{side}Score is missing")
    for key in ("current", "display", "normaltime"):
        value = score.get(key)
        if isinstance(value, int):
            return value
    raise ContractError(f"event.{side}Score has no numeric final score")


def _event_half_time_score(event: dict[str, Any], side: str) -> int:
    score = event.get(f"{side}Score")
    if not isinstance(score, dict) or not isinstance(score.get("period1"), int):
        raise ContractError(f"event.{side}Score.period1 is missing")
    return score["period1"]


def _incident_minute_key(row: dict[str, Any]) -> tuple[int, int]:
    time = row.get("time")
    added_time = row.get("addedTime")
    return (
        time if isinstance(time, int) else 10_000,
        added_time if isinstance(added_time, int) and added_time != 999 else 0,
    )


def reconcile_goals_with_scores(event: dict[str, Any], incidents: dict[str, Any]) -> dict[str, Any]:
    """Prove the chronological goal population reconstructs HT and final scores.

    SofaScore incident arrays are not trusted to be chronological. Goal incidents are
    sorted by minute/added minute, and each post-goal score must increase exactly one
    side by one. The resulting score must equal both event HT and final score fields.
    """
    goals = [row for row in _incident_rows(incidents) if row.get("incidentType") == "goal"]
    goals.sort(key=_incident_minute_key)

    home_score = 0
    away_score = 0
    half_home = 0
    half_away = 0
    chronology = []

    for goal in goals:
        next_home = goal.get("homeScore")
        next_away = goal.get("awayScore")
        if not isinstance(next_home, int) or not isinstance(next_away, int):
            raise ContractError("goal incident is missing numeric post-goal score")

        home_delta = next_home - home_score
        away_delta = next_away - away_score
        if (home_delta, away_delta) not in {(1, 0), (0, 1)}:
            raise ContractError(
                f"goal score sequence is invalid: {home_score}-{away_score} -> {next_home}-{next_away}"
            )

        home_score, away_score = next_home, next_away
        minute, added = _incident_minute_key(goal)
        if minute <= 45:
            half_home, half_away = home_score, away_score

        player = goal.get("player")
        chronology.append(
            {
                "time": minute,
                "added_time": added,
                "is_home": goal.get("isHome"),
                "sofascore_player_id": player.get("id") if isinstance(player, dict) else None,
                "home_score": home_score,
                "away_score": away_score,
            }
        )

    expected_final = (_event_score(event, "home"), _event_score(event, "away"))
    if (home_score, away_score) != expected_final:
        raise ContractError(
            f"goal incidents end {home_score}-{away_score} but event final score is "
            f"{expected_final[0]}-{expected_final[1]}"
        )

    expected_half = (_event_half_time_score(event, "home"), _event_half_time_score(event, "away"))
    if (half_home, half_away) != expected_half:
        raise ContractError(
            f"goal incidents reconstruct HT {half_home}-{half_away} but event HT score is "
            f"{expected_half[0]}-{expected_half[1]}"
        )

    return {
        "status": "PASS",
        "goal_count": len(goals),
        "half_time_score": {"home": half_home, "away": half_away},
        "final_score": {"home": home_score, "away": away_score},
        "chronology": chronology,
    }


def _substitution_key(row: dict[str, Any]) -> tuple[Any, ...]:
    player_in = row.get("playerIn")
    player_out = row.get("playerOut")
    if not isinstance(player_in, dict) or not isinstance(player_out, dict):
        raise ContractError("substitution is missing playerIn/playerOut")
    player_in_id = player_in.get("id")
    player_out_id = player_out.get("id")
    if not isinstance(player_in_id, int) or not isinstance(player_out_id, int):
        raise ContractError("substitution is missing numeric provider player IDs")
    time = row.get("time")
    if not isinstance(time, int):
        raise ContractError("substitution is missing numeric time")
    added_time = row.get("addedTime")
    return (
        row.get("isHome"),
        player_in_id,
        player_out_id,
        time,
        added_time if isinstance(added_time, int) else 0,
    )


def reconcile_substitutions(
    incidents: dict[str, Any], average_positions: dict[str, Any]
) -> dict[str, Any]:
    """Require the independent incident and average-position substitution sets to match."""
    incident_subs = [
        row for row in _incident_rows(incidents) if row.get("incidentType") == "substitution"
    ]
    position_subs = average_positions.get("substitutions")
    if not isinstance(position_subs, list):
        raise ContractError("average-positions substitutions are missing")
    position_subs = [row for row in position_subs if isinstance(row, dict)]

    incident_keys = Counter(_substitution_key(row) for row in incident_subs)
    position_keys = Counter(_substitution_key(row) for row in position_subs)
    if incident_keys != position_keys:
        missing = list((incident_keys - position_keys).elements())
        extra = list((position_keys - incident_keys).elements())
        raise ContractError(
            f"substitution populations disagree: missing_from_average_positions={missing}, "
            f"extra_in_average_positions={extra}"
        )

    return {
        "status": "PASS",
        "substitution_count": len(incident_subs),
        "home_count": sum(1 for row in incident_subs if row.get("isHome") is True),
        "away_count": sum(1 for row in incident_subs if row.get("isHome") is False),
    }


def _all_period_stat_item(statistics: dict[str, Any], name: str) -> dict[str, Any]:
    periods = statistics.get("statistics")
    if not isinstance(periods, list):
        raise ContractError("statistics.statistics is missing")
    matches = []
    for period in periods:
        if not isinstance(period, dict) or period.get("period") != "ALL":
            continue
        groups = period.get("groups")
        if not isinstance(groups, list):
            continue
        for group in groups:
            if not isinstance(group, dict):
                continue
            items = group.get("statisticsItems")
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict) and item.get("name") == name:
                    matches.append(item)
    if len(matches) != 1:
        raise ContractError(f"expected exactly one ALL statistic named {name!r}; found {len(matches)}")
    return matches[0]


def _numeric_stat_pair(statistics: dict[str, Any], name: str) -> tuple[int, int]:
    item = _all_period_stat_item(statistics, name)
    home = item.get("homeValue")
    away = item.get("awayValue")
    if not isinstance(home, int) or not isinstance(away, int):
        raise ContractError(f"statistic {name!r} does not have integer homeValue/awayValue")
    return home, away


def reconcile_cards_with_statistics(
    incidents: dict[str, Any], statistics: dict[str, Any]
) -> dict[str, Any]:
    """Cross-check yellow-card incident counts against the ALL statistics population."""
    yellow_cards = [
        row
        for row in _incident_rows(incidents)
        if row.get("incidentType") == "card" and row.get("incidentClass") == "yellow"
    ]
    incident_home = sum(1 for row in yellow_cards if row.get("isHome") is True)
    incident_away = sum(1 for row in yellow_cards if row.get("isHome") is False)
    stat_home, stat_away = _numeric_stat_pair(statistics, "Yellow cards")
    if (incident_home, incident_away) != (stat_home, stat_away):
        raise ContractError(
            f"yellow-card populations disagree: incidents={incident_home}-{incident_away}, "
            f"statistics={stat_home}-{stat_away}"
        )
    return {
        "status": "PASS",
        "yellow_cards": {"home": incident_home, "away": incident_away},
    }


def reconcile_shotmap_with_statistics(
    shotmap: dict[str, Any], statistics: dict[str, Any]
) -> dict[str, Any]:
    """Cross-check shotmap population and goal shots against aggregate statistics."""
    shots = shotmap.get("shotmap")
    if not isinstance(shots, list):
        raise ContractError("shotmap.shotmap is missing")
    shots = [row for row in shots if isinstance(row, dict)]
    home_shots = sum(1 for row in shots if row.get("isHome") is True)
    away_shots = sum(1 for row in shots if row.get("isHome") is False)
    stat_home, stat_away = _numeric_stat_pair(statistics, "Total shots")
    if (home_shots, away_shots) != (stat_home, stat_away):
        raise ContractError(
            f"shot populations disagree: shotmap={home_shots}-{away_shots}, "
            f"statistics={stat_home}-{stat_away}"
        )
    goal_shots = [row for row in shots if row.get("shotType") == "goal"]
    return {
        "status": "PASS",
        "shot_count": len(shots),
        "shots": {"home": home_shots, "away": away_shots},
        "goal_shot_count": len(goal_shots),
    }


def reconcile_goal_shots(incidents: dict[str, Any], shotmap: dict[str, Any]) -> dict[str, Any]:
    """Require every goal incident to have one matching goal shot by side/player/minute."""
    goals = [row for row in _incident_rows(incidents) if row.get("incidentType") == "goal"]
    shots = shotmap.get("shotmap")
    if not isinstance(shots, list):
        raise ContractError("shotmap.shotmap is missing")
    goal_shots = [row for row in shots if isinstance(row, dict) and row.get("shotType") == "goal"]

    def incident_goal_key(row: dict[str, Any]) -> tuple[Any, ...]:
        player = row.get("player")
        player_id = player.get("id") if isinstance(player, dict) else None
        return row.get("isHome"), player_id, row.get("time")

    def shot_goal_key(row: dict[str, Any]) -> tuple[Any, ...]:
        player = row.get("player")
        player_id = player.get("id") if isinstance(player, dict) else None
        return row.get("isHome"), player_id, row.get("time")

    incident_keys = Counter(incident_goal_key(row) for row in goals)
    shot_keys = Counter(shot_goal_key(row) for row in goal_shots)
    if incident_keys != shot_keys:
        missing = list((incident_keys - shot_keys).elements())
        extra = list((shot_keys - incident_keys).elements())
        raise ContractError(
            f"goal incident/shotmap links disagree: missing_goal_shots={missing}, "
            f"extra_goal_shots={extra}"
        )
    return {
        "status": "PASS",
        "linked_goal_count": len(goals),
    }


def reconcile_match_populations(
    *,
    event: dict[str, Any],
    incidents: dict[str, Any],
    statistics: dict[str, Any],
    shotmap: dict[str, Any],
    average_positions: dict[str, Any],
) -> dict[str, Any]:
    """Run the independent population checks required before a canonical proposal."""
    return {
        "status": "PASS",
        "goals": reconcile_goals_with_scores(event, incidents),
        "substitutions": reconcile_substitutions(incidents, average_positions),
        "cards": reconcile_cards_with_statistics(incidents, statistics),
        "shots": reconcile_shotmap_with_statistics(shotmap, statistics),
        "goal_shots": reconcile_goal_shots(incidents, shotmap),
        "database_writes": 0,
        "canonical_lufc_ids_assigned": False,
    }
