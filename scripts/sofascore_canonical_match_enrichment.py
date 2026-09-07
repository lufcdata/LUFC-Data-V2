#!/usr/bin/env python3
"""Derive safe canonical `matches` enrichment values from audited source bundles.

This module contains no network/database access and performs no writes. It is the
bridge between already-validated SofaScore evidence and established columns on the
canonical `matches` table. It deliberately excludes fields whose authoritative
routing is unresolved (for example opposition manager relations or provider IDs).
"""

from __future__ import annotations

from typing import Any, Mapping


class CanonicalMatchEnrichmentError(RuntimeError):
    """Raised when audited source bundles cannot produce safe match values."""


_REQUIRED_CANONICAL_CONTEXT = (
    "season_id",
    "competition_id",
    "competition_name_id",
    "manager_spell_id",
)


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CanonicalMatchEnrichmentError(f"{label} is missing or invalid")
    return value


def _require_int(value: Any, label: str) -> int:
    if not isinstance(value, int):
        raise CanonicalMatchEnrichmentError(f"{label} must be an integer")
    return value


def _require_pass(bundle: Mapping[str, Any], label: str) -> None:
    if bundle.get("status") != "PASS":
        raise CanonicalMatchEnrichmentError(f"{label} is not PASS")
    if bundle.get("database_writes") != 0:
        raise CanonicalMatchEnrichmentError(f"{label} reports database writes")
    if bundle.get("promotion_performed") is not False:
        raise CanonicalMatchEnrichmentError(f"{label} reports promotion")


def _first_goal(chronology: list[Any], *, leeds_is_home: bool) -> str | None:
    if not chronology:
        return None
    first = chronology[0]
    if not isinstance(first, Mapping) or not isinstance(first.get("is_home"), bool):
        raise CanonicalMatchEnrichmentError("goal chronology has no valid first-goal side")
    return "Scored" if first["is_home"] == leeds_is_home else "Conceded"


def build_canonical_match_enrichment(
    *,
    source_bundle: Mapping[str, Any],
    evidence_bundle: Mapping[str, Any],
    canonical_context: Mapping[str, Any],
) -> dict[str, Any]:
    """Return established `matches` values backed by audited source populations.

    `canonical_context` is intentionally limited to already-established LUFC lookup
    identities (season, competition naming and Leeds manager spell). Provider IDs are
    never accepted as substitutes for these canonical IDs.
    """
    _require_pass(source_bundle, "source bundle")
    _require_pass(evidence_bundle, "evidence bundle")

    if source_bundle.get("sofascore_event_id") != evidence_bundle.get("sofascore_event_id", source_bundle.get("sofascore_event_id")):
        raise CanonicalMatchEnrichmentError("source/evidence event IDs do not match")

    canonical_ids: dict[str, int] = {}
    for key in _REQUIRED_CANONICAL_CONTEXT:
        canonical_ids[key] = _require_int(canonical_context.get(key), f"canonical_context.{key}")

    leeds_is_home = source_bundle.get("leeds_is_home")
    if not isinstance(leeds_is_home, bool):
        raise CanonicalMatchEnrichmentError("source bundle has no Leeds home/away identity")

    reconciliation = _require_mapping(source_bundle.get("reconciliation"), "source_bundle.reconciliation")
    goals = _require_mapping(reconciliation.get("goals"), "source_bundle.reconciliation.goals")
    if goals.get("status") != "PASS":
        raise CanonicalMatchEnrichmentError("goal reconciliation is not PASS")

    half = _require_mapping(goals.get("half_time_score"), "goal half-time score")
    final = _require_mapping(goals.get("final_score"), "goal final score")
    half_home = _require_int(half.get("home"), "half-time home score")
    half_away = _require_int(half.get("away"), "half-time away score")
    final_home = _require_int(final.get("home"), "final home score")
    final_away = _require_int(final.get("away"), "final away score")
    chronology = goals.get("chronology")
    if not isinstance(chronology, list):
        raise CanonicalMatchEnrichmentError("goal chronology is missing")

    validations = _require_mapping(evidence_bundle.get("validations"), "evidence_bundle.validations")
    attendance = _require_mapping(validations.get("attendance"), "attendance validation")
    formations = _require_mapping(validations.get("formations"), "formation validation")
    league_position = _require_mapping(validations.get("league_position"), "league-position validation")

    attendance_value = _require_int(attendance.get("attendance"), "attendance")
    leeds_formation_side = "home" if leeds_is_home else "away"
    leeds_formation = _require_mapping(formations.get(leeds_formation_side), "Leeds formation validation")
    formation_value = str(leeds_formation.get("formation") or "").strip()
    if not formation_value:
        raise CanonicalMatchEnrichmentError("Leeds formation is missing")

    if league_position.get("status") == "NOT_APPLICABLE":
        league_position_value = None
    elif league_position.get("status") == "PASS":
        league_position_value = _require_int(league_position.get("position"), "league position")
    else:
        raise CanonicalMatchEnrichmentError("league-position validation is neither PASS nor NOT_APPLICABLE")

    leeds_half = half_home if leeds_is_home else half_away
    opponent_half = half_away if leeds_is_home else half_home
    leeds_final = final_home if leeds_is_home else final_away
    opponent_final = final_away if leeds_is_home else final_home

    values: dict[str, Any] = {
        **canonical_ids,
        "half_time_leeds_score": leeds_half,
        "half_time_opponent_score": opponent_half,
        "first_goal": _first_goal(chronology, leeds_is_home=leeds_is_home),
        "league_position_after_match": league_position_value,
        "attendance": attendance_value,
        "formation": formation_value,
    }

    return {
        "status": "PASS",
        "sofascore_event_id": source_bundle.get("sofascore_event_id"),
        "leeds_is_home": leeds_is_home,
        "reconciled_final_score": {
            "leeds": leeds_final,
            "opponent": opponent_final,
        },
        "values": values,
        "field_sources": {
            "half_time_leeds_score": "SofaScore event + reconciled goal chronology",
            "half_time_opponent_score": "SofaScore event + reconciled goal chronology",
            "first_goal": "SofaScore reconciled goal chronology",
            "league_position_after_match": "SofaScore completed-round standings",
            "attendance": str(attendance.get("source") or "").strip(),
            "formation": str(leeds_formation.get("source") or "sofascore").strip(),
            "season_id": "LUFC canonical context",
            "competition_id": "LUFC canonical context",
            "competition_name_id": "LUFC canonical context",
            "manager_spell_id": "LUFC canonical context",
        },
        "database_writes": 0,
        "canonical_promotion_performed": False,
    }
