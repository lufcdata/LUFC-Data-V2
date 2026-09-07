#!/usr/bin/env python3
"""Build audited zero-write proposals for structured opposition goals.

The canonical `opposition_goals` destination is a PROPOSED schema contract and is not
currently deployed. Consequently this adapter can prove the exact rows that would be
needed, but it deliberately returns SCHEMA_GAP/BLOCKED until the destination is
approved and deployed.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence


class OppositionGoalDiffError(RuntimeError):
    """Raised when opposition-goal evidence cannot be proposed safely."""


def _require_int(value: Any, label: str) -> int:
    if not isinstance(value, int):
        raise OppositionGoalDiffError(f"{label} must be an integer")
    return value


def _minute_raw(minute: int, added: int) -> str:
    return f"{minute}+{added}" if added else str(minute)


def _game_state_before(leeds_score: int, opponent_score: int) -> str:
    delta = leeds_score - opponent_score
    if delta == 0:
        return "Level"
    if delta > 0:
        return f"Leading +{delta}"
    return f"Trailing {delta}"


def build_opposition_goal_proposal(
    *,
    canonical_match_id: int,
    staged_events: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive exact opposition-goal rows from the audited staged event population."""
    match_id = _require_int(canonical_match_id, "canonical match ID")
    if staged_events.get("database_writes") != 0 or staged_events.get("promotion_performed") is not False:
        raise OppositionGoalDiffError("staged event population is not zero-write")

    rows = staged_events.get("events")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise OppositionGoalDiffError("staged event population has no events")

    goals = [row for row in rows if isinstance(row, Mapping) and row.get("event_kind") == "goal"]
    if not goals:
        raise OppositionGoalDiffError("staged event population has no goal events")

    leeds_score = 0
    opponent_score = 0
    opposition_number = 0
    operations: list[dict[str, Any]] = []

    for sequence, goal in enumerate(goals, start=1):
        side = goal.get("team_side")
        if side not in {"LEEDS", "OPPONENT"}:
            raise OppositionGoalDiffError("goal event has invalid team_side")
        minute = _require_int(goal.get("minute_base"), "goal minute_base")
        added = goal.get("stoppage_minute")
        if added is None:
            added = 0
        added = _require_int(added, "goal stoppage_minute")
        if minute < 0 or added < 0:
            raise OppositionGoalDiffError("goal timing cannot be negative")

        before_leeds = leeds_score
        before_opponent = opponent_score
        if side == "LEEDS":
            leeds_score += 1
            continue

        opponent_score += 1
        opposition_number += 1
        event_json = goal.get("event_json")
        if not isinstance(event_json, Mapping):
            raise OppositionGoalDiffError("opposition goal has no source event_json")
        player = event_json.get("player")
        if not isinstance(player, Mapping):
            raise OppositionGoalDiffError("opposition goal has no scorer object")
        scorer = str(player.get("name") or player.get("shortName") or "").strip()
        if not scorer:
            raise OppositionGoalDiffError("opposition goal scorer name is missing")
        assist = event_json.get("assist1")
        assist_name = None
        if isinstance(assist, Mapping):
            assist_name = str(assist.get("name") or assist.get("shortName") or "").strip() or None

        is_own_goal = bool(event_json.get("incidentClass") == "ownGoal" or event_json.get("goalType") == "ownGoal")
        operation = {
            "table": "opposition_goals",
            "action": "INSERT_AFTER_PARENT_KEY_ALLOCATION_AND_SCHEMA_DEPLOYMENT",
            "key": {
                "match_id": match_id,
                "opposition_goal_number_in_match": opposition_number,
            },
            "values": {
                "match_id": match_id,
                "sequence_in_match": sequence,
                "opposition_goal_number_in_match": opposition_number,
                "scorer_name_raw": scorer,
                "assist_name_raw": assist_name,
                "minute_raw": _minute_raw(minute, added),
                "minute_normalised": minute,
                "stoppage_minute": added or None,
                "period": goal.get("period"),
                "is_own_goal": is_own_goal,
                "score_leeds_after": leeds_score,
                "score_opponent_after": opponent_score,
                "game_state_before": _game_state_before(before_leeds, before_opponent),
                "ingestion_run_id": "<FROM_PARENT_INSERT>",
            },
            "deferred_parent_key": {
                "column": "ingestion_run_id",
                "from_operation": "ingestion.runs",
                "allocation": "FROM_PARENT_INSERT",
            },
            "provider_evidence": {
                "provider": goal.get("provider"),
                "provider_event_id": goal.get("provider_event_id"),
                "provider_team_id": goal.get("provider_team_id"),
                "provider_player_id": goal.get("provider_player_id"),
                "provider_secondary_player_id": goal.get("provider_secondary_player_id"),
            },
            "canonical_primary_key_allocated": False,
        }
        operations.append(operation)

    return {
        "status": "SCHEMA_GAP",
        "canonical_destination": "opposition_goals",
        "destination_deployed": False,
        "canonical_match_id": match_id,
        "opposition_goal_count": opposition_number,
        "operations": operations,
        "operation_count": len(operations),
        "blocker": "structured opposition goals destination and parent ingestion run are not deployed",
        "database_writes": 0,
        "sql_generated": False,
        "promotion_performed": False,
    }
