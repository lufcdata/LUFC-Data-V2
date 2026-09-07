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

    player = captain.get("player")
    if not isinstance(player, dict):
        raise ContractError(f"lineups.{side} captain has no player object")

    provider_player_id = player.get("id")
    if not isinstance(provider_player_id, int):
        raise ContractError(f"lineups.{side} captain has no numeric SofaScore player ID")

    return {
        "provider": "sofascore",
        "sofascore_player_id": provider_player_id,
        "name": str(player.get("name") or ""),
        "shirt_number": captain.get("shirtNumber"),
        "match_position": captain.get("position"),
        "substitute": False,
        "captain": True,
    }
