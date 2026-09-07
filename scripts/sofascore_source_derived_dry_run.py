#!/usr/bin/env python3
"""Derive a zero-write fixture validation bundle directly from captured SofaScore payloads.

This module removes manually assembled reconciliation/staging summaries from the dry-run
path. It accepts already-captured raw payload objects, derives fixture side, validates
lineups, reconciles independent event populations and builds the complete staged-event
population. It has no network or database access and assigns no canonical LUFC IDs.
"""

from __future__ import annotations

from typing import Any, Mapping

from sofascore_dry_run_contract import reconcile_match_populations, summarize_lineups
from sofascore_staged_events import build_staged_event_population


class SourceDerivedDryRunError(RuntimeError):
    """Raised when captured payloads cannot form one deterministic dry-run bundle."""


def _require_mapping(payloads: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = payloads.get(key)
    if not isinstance(value, Mapping):
        raise SourceDerivedDryRunError(f"required raw payload is missing or invalid: {key}")
    return value


def _require_int(value: Any, label: str) -> int:
    if not isinstance(value, int):
        raise SourceDerivedDryRunError(f"{label} must be an integer")
    return value


def _team_id(event: Mapping[str, Any], side: str) -> int:
    team = event.get(f"{side}Team")
    if not isinstance(team, Mapping):
        raise SourceDerivedDryRunError(f"event.{side}Team is missing")
    return _require_int(team.get("id"), f"event.{side}Team.id")


def build_source_derived_dry_run(
    *,
    raw_payloads: Mapping[str, Any],
    leeds_team_provider_id: int,
) -> dict[str, Any]:
    """Return source-derived reconciliation + staged events with zero canonical writes."""
    event = _require_mapping(raw_payloads, "event")
    lineups = _require_mapping(raw_payloads, "lineups")
    incidents = _require_mapping(raw_payloads, "incidents")
    statistics = _require_mapping(raw_payloads, "statistics")
    shotmap = _require_mapping(raw_payloads, "shotmap")
    average_positions = _require_mapping(raw_payloads, "average_positions")

    event_id = _require_int(event.get("id"), "event.id")
    home_team_provider_id = _team_id(event, "home")
    away_team_provider_id = _team_id(event, "away")
    if leeds_team_provider_id not in {home_team_provider_id, away_team_provider_id}:
        raise SourceDerivedDryRunError("Leeds provider team ID is not one of the event teams")
    leeds_is_home = leeds_team_provider_id == home_team_provider_id

    lineup_summary = summarize_lineups(dict(lineups))
    reconciliation = reconcile_match_populations(
        event=dict(event),
        incidents=dict(incidents),
        statistics=dict(statistics),
        shotmap=dict(shotmap),
        average_positions=dict(average_positions),
    )

    incident_rows = incidents.get("incidents")
    if not isinstance(incident_rows, list):
        raise SourceDerivedDryRunError("incidents.incidents is missing")
    shot_rows = shotmap.get("shotmap")
    if not isinstance(shot_rows, list):
        raise SourceDerivedDryRunError("shotmap.shotmap is missing")

    staged_events = build_staged_event_population(
        incidents=[row for row in incident_rows if isinstance(row, Mapping)],
        shots=[row for row in shot_rows if isinstance(row, Mapping)],
        leeds_is_home=leeds_is_home,
        home_team_provider_id=home_team_provider_id,
        away_team_provider_id=away_team_provider_id,
    )

    validations = {
        "lineups": {"status": "PASS", "squad_count_home": lineup_summary["home"]["squad_count"], "squad_count_away": lineup_summary["away"]["squad_count"]},
        "goals": {"status": reconciliation["goals"]["status"], "goal_count": reconciliation["goals"]["goal_count"]},
        "scores": {"status": reconciliation["goals"]["status"], "half_time_score": reconciliation["goals"]["half_time_score"], "final_score": reconciliation["goals"]["final_score"]},
        "substitutions": {"status": reconciliation["substitutions"]["status"], "substitution_count": reconciliation["substitutions"]["substitution_count"]},
        "cards": {"status": reconciliation["cards"]["status"], "yellow_cards": reconciliation["cards"]["yellow_cards"]},
        "shots": {"status": reconciliation["shots"]["status"], "shot_count": reconciliation["shots"]["shot_count"], "shots": reconciliation["shots"]["shots"]},
        "staged_events": {"status": staged_events["status"], "event_count": staged_events["event_count"]},
    }

    return {
        "status": "PASS",
        "provider": "sofascore",
        "sofascore_event_id": event_id,
        "home_team_provider_id": home_team_provider_id,
        "away_team_provider_id": away_team_provider_id,
        "leeds_team_provider_id": leeds_team_provider_id,
        "leeds_is_home": leeds_is_home,
        "lineups": lineup_summary,
        "reconciliation": reconciliation,
        "staged_events": staged_events,
        "validations": validations,
        "database_writes": 0,
        "canonical_lufc_ids_assigned": False,
        "promotion_performed": False,
    }
