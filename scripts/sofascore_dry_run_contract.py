#!/usr/bin/env python3
"""Pure validation helpers for read-only SofaScore ingestion dry runs.

No network or database access lives here. These helpers operate only on already
captured SofaScore payloads and return explicit PASS / N/A / BLOCKED semantics.
"""

from __future__ import annotations

from typing import Any

# Fail closed: only competitions explicitly classified as leagues may trigger a
# post-match league-position lookup. Add future league competitions deliberately.
LEAGUE_COMPETITION_NAMES = {"premier league"}


class ContractError(RuntimeError):
    """Raised when a captured payload cannot satisfy the ingestion contract."""


def competition_name(event: dict[str, Any]) -> str:
    tournament = event.get("tournament")
    if not isinstance(tournament, dict):
        return ""
    return str(tournament.get("name") or "")


def league_position_requirement(event: dict[str, Any]) -> dict[str, str]:
    """Return whether the fixture should have a league-position lookup.

    Non-league fixtures are explicitly N/A rather than missing. Unknown competition
    names fail closed as non-league until deliberately classified.
    """
    name = competition_name(event)
    if name.casefold() in LEAGUE_COMPETITION_NAMES:
        return {
            "status": "REQUIRED",
            "reason": f"league fixture: {name}",
        }
    return {
        "status": "NOT_APPLICABLE",
        "reason": f"non-league fixture: {name or 'unknown competition'}",
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
