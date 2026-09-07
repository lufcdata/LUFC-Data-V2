#!/usr/bin/env python3
"""Build an auditable proposed LUFC canonical diff without database writes.

The builder is deliberately conservative. It only proposes writes to canonical
surfaces that already have an explicit destination in the LUFC schema contract.
Required source facts that do not yet have a safe canonical destination are emitted
as SCHEMA_GAP blockers instead of being discarded, overloaded into unrelated fields,
or written to an improvised location.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping


class CanonicalDiffError(RuntimeError):
    """Raised when a proposed canonical diff cannot be formed safely."""


def _require_int(value: Any, label: str) -> int:
    if not isinstance(value, int):
        raise CanonicalDiffError(f"{label} must be an integer")
    return value


def _require_text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise CanonicalDiffError(f"{label} is required")
    return text


def _resolved_id(package: Mapping[str, Any], entity_type: str, provider_id: int) -> int:
    """Read one canonical ID from an already-validated identity package."""
    if entity_type == "match":
        match = package.get("match")
        if not isinstance(match, Mapping):
            raise CanonicalDiffError("identity package has no match resolution")
        if match.get("provider_id") != provider_id:
            raise CanonicalDiffError("identity package match provider ID does not match fixture")
        return _require_int(match.get("canonical_id"), "canonical match ID")

    plural = {"team": "teams", "player": "players", "manager": "managers"}.get(entity_type)
    if plural is None:
        raise CanonicalDiffError(f"unsupported identity entity type: {entity_type}")
    group = package.get(plural)
    if not isinstance(group, Mapping):
        raise CanonicalDiffError(f"identity package has no {plural} resolution group")
    resolutions = group.get("resolutions")
    if not isinstance(resolutions, list):
        raise CanonicalDiffError(f"identity package {plural}.resolutions is missing")
    matches = [
        row for row in resolutions
        if isinstance(row, Mapping) and row.get("provider_id") == provider_id
    ]
    if len(matches) != 1:
        raise CanonicalDiffError(
            f"expected exactly one {entity_type} identity for provider_id={provider_id}; found {len(matches)}"
        )
    return _require_int(matches[0].get("canonical_id"), f"canonical {entity_type} ID")


def _operation(table: str, action: str, key: Mapping[str, Any], values: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "table": table,
        "action": action,
        "key": dict(key),
        "values": dict(values),
    }


def _schema_gap(domain: str, field: str, reason: str, source: str) -> dict[str, str]:
    return {
        "status": "SCHEMA_GAP",
        "domain": domain,
        "field": field,
        "reason": reason,
        "source": source,
    }


def build_proposed_canonical_diff(
    *,
    fixture: Mapping[str, Any],
    identity_package: Mapping[str, Any],
    leeds_team_provider_id: int,
    leeds_manager_provider_id: int,
    leeds_captain_provider_id: int,
    leeds_players: Iterable[Mapping[str, Any]],
    leeds_substitutions: Iterable[Mapping[str, Any]],
    leeds_goals: Iterable[Mapping[str, Any]],
    opposition_goals: Iterable[Mapping[str, Any]],
    opposition_manager_provider_id: int,
    opposition_captain_provider_id: int,
    attendance_source: str,
) -> dict[str, Any]:
    """Return a table-by-table proposed diff and explicit unresolved schema gaps.

    No SQL is generated and no database connection exists here. The result is a
    proposal for review by the promotion gate, not permission to write.
    """
    event_id = _require_int(fixture.get("event_id"), "SofaScore event ID")
    canonical_match_id = _resolved_id(identity_package, "match", event_id)

    home_team_provider_id = _require_int(fixture.get("home_team_provider_id"), "home team provider ID")
    away_team_provider_id = _require_int(fixture.get("away_team_provider_id"), "away team provider ID")
    if leeds_team_provider_id not in {home_team_provider_id, away_team_provider_id}:
        raise CanonicalDiffError("Leeds provider team ID is not one of the fixture teams")

    leeds_home = leeds_team_provider_id == home_team_provider_id
    opponent_provider_id = away_team_provider_id if leeds_home else home_team_provider_id
    opponent_id = _resolved_id(identity_package, "team", opponent_provider_id)
    leeds_manager_id = _resolved_id(identity_package, "manager", leeds_manager_provider_id)
    leeds_captain_id = _resolved_id(identity_package, "player", leeds_captain_provider_id)
    opposition_manager_id = _resolved_id(identity_package, "manager", opposition_manager_provider_id)
    opposition_captain_id = _resolved_id(identity_package, "player", opposition_captain_provider_id)

    home_score = _require_int(fixture.get("home_score"), "home score")
    away_score = _require_int(fixture.get("away_score"), "away score")
    leeds_score = home_score if leeds_home else away_score
    opponent_score = away_score if leeds_home else home_score
    result = "W" if leeds_score > opponent_score else "L" if leeds_score < opponent_score else "D"

    operations: list[dict[str, Any]] = []
    operations.append(
        _operation(
            "matches",
            "INSERT",
            {"match_id": canonical_match_id},
            {
                "match_date": _require_text(fixture.get("match_date"), "match date"),
                "opponent_id": opponent_id,
                "venue_type": "H" if leeds_home else "A",
                "leeds_score": leeds_score,
                "opponent_score": opponent_score,
                "result": result,
                "stadium": _require_text(fixture.get("stadium"), "stadium"),
                "attendance": _require_int(fixture.get("attendance"), "attendance"),
                "referee": _require_text(fixture.get("referee"), "referee"),
                "kickoff_time": _require_text(fixture.get("kickoff_time"), "kick-off time"),
                "round": _require_text(fixture.get("round"), "round"),
                "formation": _require_text(fixture.get("leeds_formation"), "Leeds formation"),
                "captain_player_id": leeds_captain_id,
            },
        )
    )

    lineup_rows = list(leeds_players)
    if len(lineup_rows) != 20:
        raise CanonicalDiffError(f"Leeds matchday squad must contain 20 players; found {len(lineup_rows)}")
    starters = [row for row in lineup_rows if row.get("started") is True]
    if len(starters) != 11:
        raise CanonicalDiffError(f"Leeds XI must contain 11 starters; found {len(starters)}")

    for index, row in enumerate(lineup_rows, start=1):
        provider_player_id = _require_int(row.get("provider_player_id"), "lineup provider player ID")
        player_id = _resolved_id(identity_package, "player", provider_player_id)
        started = row.get("started") is True
        substitute = row.get("substitute") is True
        if started == substitute:
            raise CanonicalDiffError(
                f"player provider_id={provider_player_id} must be exactly one of started/substitute"
            )
        operations.append(
            _operation(
                "player_matches",
                "INSERT",
                {"match_id": canonical_match_id, "player_id": player_id},
                {
                    "started": started,
                    "substitute": substitute,
                    "lineup_order": index if index <= 17 else None,
                    "source_slot": row.get("source_slot"),
                },
            )
        )

    for row in leeds_goals:
        provider_player_id = _require_int(row.get("provider_player_id"), "goal scorer provider player ID")
        scorer_id = _resolved_id(identity_package, "player", provider_player_id)
        assist_provider_id = row.get("assist_provider_player_id")
        assist_id = (
            _resolved_id(identity_package, "player", assist_provider_id)
            if isinstance(assist_provider_id, int)
            else None
        )
        operations.append(
            _operation(
                "goals",
                "INSERT",
                {"match_id": canonical_match_id, "provider_event_id": row.get("provider_event_id")},
                {
                    "leeds_player_id": scorer_id,
                    "scorer_name_raw": _require_text(row.get("scorer_name"), "goal scorer name"),
                    "minute_raw": _require_text(row.get("minute_raw"), "goal minute"),
                    "minute_normalised": _require_int(row.get("minute_normalised"), "goal minute normalised"),
                    "is_own_goal": row.get("is_own_goal") is True,
                    "assist_player_id": assist_id,
                    "assisted_by_raw": row.get("assist_name"),
                    "goal_type": row.get("goal_type"),
                    "location": row.get("location"),
                    "body_part": row.get("body_part"),
                    "goal_state": row.get("goal_state"),
                    "game_state": row.get("game_state"),
                },
            )
        )

    schema_gaps: list[dict[str, str]] = []
    if list(opposition_goals):
        schema_gaps.append(
            _schema_gap(
                "goals",
                "structured opposition goals",
                "current goals table is Leeds-scorer-oriented and has no explicit opposition scorer identity destination",
                "SofaScore incidents + shotmap",
            )
        )

    if list(leeds_substitutions):
        schema_gaps.append(
            _schema_gap(
                "substitutions",
                "post-match substitution ingestion",
                "existing historical substitution population needs an explicitly verified insert contract before automated promotion",
                "SofaScore incidents + average-positions",
            )
        )

    schema_gaps.extend(
        [
            _schema_gap(
                "match",
                "opposition manager",
                f"resolved canonical opposition manager/person identity {opposition_manager_id} must be routed through the authoritative managerial assignment model",
                "SofaScore managers",
            ),
            _schema_gap(
                "match",
                "opposition captain",
                f"resolved canonical opposition captain player identity {opposition_captain_id} has no verified canonical match destination yet",
                "SofaScore lineups",
            ),
            _schema_gap(
                "match",
                "attendance provenance",
                f"attendance value is sourced from {attendance_source}, but field-level provenance requires a purpose-built ingestion provenance layer",
                attendance_source,
            ),
            _schema_gap(
                "match",
                "SofaScore external event identity",
                "provider event ID must live in the external identity/provenance layer, never in matches.match_id",
                "SofaScore event",
            ),
            _schema_gap(
                "positions",
                "exact tactical formation slots",
                "SofaScore supplies broad match positions and average coordinates but no exact RCB/LWB/etc slot labels",
                "SofaScore lineups + average-positions",
            ),
        ]
    )

    return {
        "status": "BLOCKED" if schema_gaps else "PASS",
        "sofascore_event_id": event_id,
        "canonical_match_id": canonical_match_id,
        "operation_count": len(operations),
        "operations": operations,
        "schema_gap_count": len(schema_gaps),
        "schema_gaps": schema_gaps,
        "database_writes": 0,
        "sql_generated": False,
        "promotion_performed": False,
    }
