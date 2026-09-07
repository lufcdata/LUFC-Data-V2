#!/usr/bin/env python3
"""Pure validation helpers for read-only SofaScore ingestion dry runs.

No network or database access lives here. These helpers operate only on already
captured provider payloads and return explicit PASS / N/A / BLOCKED semantics.
"""

from __future__ import annotations

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
