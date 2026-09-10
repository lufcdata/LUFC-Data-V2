#!/usr/bin/env python3
"""Build an auditable proposed LUFC canonical diff without database writes.

The builder is deliberately conservative. It only proposes writes to canonical
surfaces that already have an explicit destination in the LUFC schema contract.
Required source facts that do not yet have a safe canonical destination are emitted
as SCHEMA_GAP blockers instead of being discarded, overloaded into unrelated fields,
or written to an improvised location.

Identity resolution is LUFC-scoped: Leeds players resolve to `players`, the opponent
club resolves to `clubs`, Leeds managers resolve to `managers`, and opposition managers
resolve to `managerial_people`. Opposition players are never forced into `players`.
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


def _require_scoped_resolution(
    package: Mapping[str, Any],
    *,
    key: str,
    entity_scope: str,
    provider_id: int,
) -> int:
    resolution = package.get(key)
    if not isinstance(resolution, Mapping):
        raise CanonicalDiffError(f"identity package has no {key} resolution")
    if resolution.get("entity_scope") != entity_scope:
        raise CanonicalDiffError(
            f"identity package {key} scope is {resolution.get('entity_scope')!r}; expected {entity_scope!r}"
        )
    if resolution.get("provider_id") != provider_id:
        raise CanonicalDiffError(
            f"identity package {key} provider ID does not match provider_id={provider_id}"
        )
    return _require_int(resolution.get("canonical_id"), f"canonical {entity_scope} ID")


def _resolved_leeds_player(package: Mapping[str, Any], provider_id: int) -> int:
    group = package.get("leeds_players")
    if not isinstance(group, Mapping):
        raise CanonicalDiffError("identity package has no leeds_players resolution group")
    resolutions = group.get("resolutions")
    if not isinstance(resolutions, list):
        raise CanonicalDiffError("identity package leeds_players.resolutions is missing")
    matches = [
        row
        for row in resolutions
        if isinstance(row, Mapping)
        and row.get("entity_scope") == "leeds_player"
        and row.get("provider_id") == provider_id
    ]
    if len(matches) != 1:
        raise CanonicalDiffError(
            f"expected exactly one Leeds player identity for provider_id={provider_id}; found {len(matches)}"
        )
    return _require_int(matches[0].get("canonical_id"), "canonical Leeds player ID")


def _validate_leeds_team_identity(package: Mapping[str, Any], provider_id: int) -> None:
    identity = package.get("leeds_team")
    if not isinstance(identity, Mapping):
        raise CanonicalDiffError("identity package has no leeds_team validation")
    if identity.get("provider_id") != provider_id:
        raise CanonicalDiffError("identity package Leeds team provider ID does not match fixture")
    if identity.get("canonical_mapping") != "NOT_APPLICABLE":
        raise CanonicalDiffError("Leeds team must not be mapped into opponent clubs")


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


def _substitution_minute(row: Mapping[str, Any]) -> tuple[str, int, int | None, str]:
    minute_base = row.get("minute_base")
    stoppage = row.get("stoppage_minute")
    minute_raw = row.get("minute_raw")

    if not isinstance(minute_base, int):
        fallback = row.get("minute")
        if isinstance(fallback, int):
            minute_base = fallback
        elif isinstance(fallback, str) and fallback.strip().rstrip("'").isdigit():
            minute_base = int(fallback.strip().rstrip("'"))
        else:
            raise CanonicalDiffError("substitution minute_base is required")
    if minute_base < 0:
        raise CanonicalDiffError("substitution minute_base cannot be negative")
    if stoppage is not None and (not isinstance(stoppage, int) or stoppage < 0):
        raise CanonicalDiffError("substitution stoppage_minute must be a non-negative integer")

    if isinstance(minute_raw, str) and minute_raw.strip():
        raw = minute_raw.strip()
    elif stoppage:
        raw = f"{minute_base}+{stoppage}'"
    else:
        raw = f"{minute_base}'"

    if minute_base == 46 and not stoppage:
        phase = "half_time"
    elif minute_base <= 45:
        phase = "first_half"
    else:
        phase = "second_half"
    return raw, minute_base, stoppage, phase


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
    canonical_match_id = _require_scoped_resolution(
        identity_package,
        key="match",
        entity_scope="match",
        provider_id=event_id,
    )

    home_team_provider_id = _require_int(fixture.get("home_team_provider_id"), "home team provider ID")
    away_team_provider_id = _require_int(fixture.get("away_team_provider_id"), "away team provider ID")
    if leeds_team_provider_id not in {home_team_provider_id, away_team_provider_id}:
        raise CanonicalDiffError("Leeds provider team ID is not one of the fixture teams")
    _validate_leeds_team_identity(identity_package, leeds_team_provider_id)

    leeds_home = leeds_team_provider_id == home_team_provider_id
    opponent_provider_id = away_team_provider_id if leeds_home else home_team_provider_id
    opponent_id = _require_scoped_resolution(
        identity_package,
        key="opponent_club",
        entity_scope="opponent_club",
        provider_id=opponent_provider_id,
    )
    leeds_manager_id = _require_scoped_resolution(
        identity_package,
        key="leeds_manager",
        entity_scope="leeds_manager",
        provider_id=leeds_manager_provider_id,
    )
    opposition_manager_id = _require_scoped_resolution(
        identity_package,
        key="opposition_manager",
        entity_scope="opposition_manager",
        provider_id=opposition_manager_provider_id,
    )
    leeds_captain_id = _resolved_leeds_player(identity_package, leeds_captain_provider_id)

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
    substitution_rows = list(leeds_substitutions)
    starters = [row for row in lineup_rows if row.get("started") is True]
    if len(starters) != 11:
        raise CanonicalDiffError(f"Leeds XI must contain 11 starters; found {len(starters)}")

    provider_ids: list[int] = []
    substitute_provider_ids: set[int] = set()
    for row in lineup_rows:
        provider_player_id = _require_int(row.get("provider_player_id"), "lineup provider player ID")
        started = row.get("started") is True
        substitute = row.get("substitute") is True
        if started == substitute:
            raise CanonicalDiffError(
                f"player provider_id={provider_player_id} must be exactly one of started/substitute"
            )
        provider_ids.append(provider_player_id)
        if substitute:
            substitute_provider_ids.add(provider_player_id)

    if len(provider_ids) != len(set(provider_ids)):
        raise CanonicalDiffError("Leeds appearance population contains duplicate provider player IDs")

    proven_player_on_ids = {
        _require_int(row.get("player_in"), "substitution player_in provider ID")
        for row in substitution_rows
    }
    if len(proven_player_on_ids) != len(substitution_rows):
        raise CanonicalDiffError("Leeds substitution population contains duplicate player-on identities")
    if substitute_provider_ids != proven_player_on_ids:
        raise CanonicalDiffError(
            "Leeds substitute appearance population must exactly match proven substitution player-on population"
        )
    if len(lineup_rows) != 11 + len(proven_player_on_ids):
        raise CanonicalDiffError(
            "Leeds appearance population must equal 11 starters plus distinct proven players-on"
        )

    for index, row in enumerate(lineup_rows, start=1):
        provider_player_id = _require_int(row.get("provider_player_id"), "lineup provider player ID")
        player_id = _resolved_leeds_player(identity_package, provider_player_id)
        started = row.get("started") is True
        substitute = row.get("substitute") is True
        operation = _operation(
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
        operation["provider_evidence"] = {
            "provider": "sofascore",
            "provider_event_id": event_id,
            "provider_player_id": provider_player_id,
        }
        operations.append(operation)

    for row in leeds_goals:
        provider_player_id = _require_int(row.get("provider_player_id"), "goal scorer provider player ID")
        scorer_id = _resolved_leeds_player(identity_package, provider_player_id)
        assist_provider_id = row.get("assist_provider_player_id")
        assist_id = (
            _resolved_leeds_player(identity_package, assist_provider_id)
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

    for row in substitution_rows:
        off_provider_id = _require_int(row.get("player_out"), "substitution player_out provider ID")
        on_provider_id = _require_int(row.get("player_in"), "substitution player_in provider ID")
        if off_provider_id == on_provider_id:
            raise CanonicalDiffError("substitution player_out and player_in must be different")
        player_off_id = _resolved_leeds_player(identity_package, off_provider_id)
        player_on_id = _resolved_leeds_player(identity_package, on_provider_id)
        minute_raw, minute_base, stoppage_minute, timing_phase = _substitution_minute(row)
        operations.append(
            _operation(
                "match_substitutions",
                "INSERT",
                {
                    "match_id": canonical_match_id,
                    "player_off_id": player_off_id,
                    "player_on_id": player_on_id,
                    "minute_base": minute_base,
                    "stoppage_minute": stoppage_minute,
                },
                {
                    "minute_raw": minute_raw,
                    "minute_base": minute_base,
                    "stoppage_minute": stoppage_minute,
                    "timing_phase": timing_phase,
                    "timing_known": True,
                    "relationship_status": "proven",
                    "evidence": "direct_source",
                    "note": "SofaScore incidents reconciled against average-positions substitution population",
                    "source_fragment": row.get("source_fragment"),
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

    schema_gaps.extend(
        [
            _schema_gap(
                "match",
                "opposition manager",
                f"resolved managerial_people identity {opposition_manager_id} must be routed through the authoritative managerial assignment model",
                "SofaScore managers",
            ),
            _schema_gap(
                "match",
                "opposition captain",
                f"SofaScore opposition captain provider identity {opposition_captain_provider_id} has no approved canonical destination; it must not be inserted into Leeds players",
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
        "validated_leeds_manager_id": leeds_manager_id,
        "validated_opposition_managerial_person_id": opposition_manager_id,
        "leeds_substitution_operation_count": len(substitution_rows),
        "operation_count": len(operations),
        "operations": operations,
        "schema_gap_count": len(schema_gaps),
        "schema_gaps": schema_gaps,
        "identity_scope": "LUFC_SCOPED",
        "opposition_players_mapped_to_leeds_players": False,
        "database_writes": 0,
        "sql_generated": False,
        "promotion_performed": False,
    }
