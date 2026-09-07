#!/usr/bin/env python3
"""Build the proposed LUFC canonical diff directly from audited SofaScore source bundles.

This is the source-to-canonical proposal adapter. It converts already-reconciled raw
capture facts into the narrow input contract of `sofascore_canonical_diff`, then applies
canonical match enrichment. It performs no network/database access and no writes.

Provider taxonomies are not silently translated into LUFC taxonomies: goal type,
location and body-part canonical fields remain unset until an explicit mapping contract
is approved. Opposition goals remain structured schema-gap evidence.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from sofascore_canonical_diff import build_proposed_canonical_diff
from sofascore_canonical_match_enrichment import (
    build_canonical_match_enrichment,
    merge_match_enrichment_into_canonical_diff,
)
from sofascore_goal_semantics import derive_leeds_goal_semantics


class SourceCanonicalDiffError(RuntimeError):
    """Raised when audited source facts cannot form a deterministic canonical proposal."""


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SourceCanonicalDiffError(f"{label} is missing or invalid")
    return value


def _integer(value: Any, label: str) -> int:
    if not isinstance(value, int):
        raise SourceCanonicalDiffError(f"{label} must be an integer")
    return value


def _text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise SourceCanonicalDiffError(f"{label} is missing")
    return text


def _event_datetime(event: Mapping[str, Any]) -> datetime:
    timestamp = event.get("startTimestamp")
    if not isinstance(timestamp, (int, float)):
        raise SourceCanonicalDiffError("event.startTimestamp is missing")
    return datetime.fromtimestamp(timestamp, tz=ZoneInfo("UTC")).astimezone(
        ZoneInfo("Europe/London")
    )


def _venue_name(event: Mapping[str, Any]) -> str:
    venue = _mapping(event.get("venue"), "event.venue")
    stadium = venue.get("stadium")
    if isinstance(stadium, Mapping) and isinstance(stadium.get("name"), str):
        name = stadium["name"].strip()
        if name:
            return name
    return _text(venue.get("name"), "event.venue name")


def _referee_name(event: Mapping[str, Any]) -> str:
    referee = _mapping(event.get("referee"), "event.referee")
    return _text(referee.get("name"), "event.referee.name")


def _source_player_name(row: Mapping[str, Any], key: str = "player") -> str:
    player = _mapping(row.get(key), f"goal {key}")
    return _text(player.get("name"), f"goal {key}.name")


def _source_player_id(row: Mapping[str, Any], key: str = "player") -> int:
    player = _mapping(row.get(key), f"event {key}")
    return _integer(player.get("id"), f"event {key}.id")


def _minute_raw(minute: int, added: int) -> str:
    return f"{minute}+{added}" if added > 0 else str(minute)


def _lineup_rows(source_bundle: Mapping[str, Any], leeds_side: str) -> list[dict[str, Any]]:
    lineups = _mapping(source_bundle.get("lineups"), "source_bundle.lineups")
    side = _mapping(lineups.get(leeds_side), f"source_bundle.lineups.{leeds_side}")
    starters = side.get("starters")
    bench = side.get("bench")
    if not isinstance(starters, list) or not isinstance(bench, list):
        raise SourceCanonicalDiffError("Leeds lineup starter/bench populations are missing")
    if len(starters) != 11:
        raise SourceCanonicalDiffError("Leeds lineup must contain exactly 11 starters")

    populations = _mapping(source_bundle.get("appearance_population"), "source_bundle.appearance_population")
    population = _mapping(populations.get(leeds_side), f"source_bundle.appearance_population.{leeds_side}")
    used_ids = population.get("used_substitute_ids")
    appearance_ids = population.get("appearance_ids")
    if not isinstance(used_ids, list) or not all(isinstance(value, int) for value in used_ids):
        raise SourceCanonicalDiffError("Leeds used-substitute appearance population is missing")
    if not isinstance(appearance_ids, list) or not all(isinstance(value, int) for value in appearance_ids):
        raise SourceCanonicalDiffError("Leeds authoritative appearance population is missing")
    used_set = set(used_ids)
    appearance_set = set(appearance_ids)

    starter_ids = {
        _integer(_mapping(row, "starter").get("sofascore_player_id"), "starter provider player ID")
        for row in starters
    }
    bench_by_id = {
        _integer(_mapping(row, "bench player").get("sofascore_player_id"), "bench provider player ID"): row
        for row in bench
    }
    if not used_set.issubset(bench_by_id):
        raise SourceCanonicalDiffError("Leeds used-substitute population is not contained in named bench")
    if appearance_set != starter_ids | used_set:
        raise SourceCanonicalDiffError("Leeds appearance population does not equal starters plus proven players-on")

    used_bench = [row for row in bench if _integer(_mapping(row, "bench player").get("sofascore_player_id"), "bench provider player ID") in used_set]
    result: list[dict[str, Any]] = []
    for bucket, rows in (("XI", starters), ("SUB", used_bench)):
        for index, raw in enumerate(rows, start=1):
            row = _mapping(raw, "lineup player")
            shirt_number = row.get("shirt_number")
            if not isinstance(shirt_number, int):
                jersey = row.get("jersey_number")
                shirt_number = jersey if isinstance(jersey, int) else None
            result.append(
                {
                    "provider_player_id": _integer(
                        row.get("sofascore_player_id"), "lineup provider player ID"
                    ),
                    "started": bucket == "XI",
                    "substitute": bucket == "SUB",
                    "source_slot": f"{bucket}{index}",
                    "shirt_number": shirt_number,
                }
            )
    if {row["provider_player_id"] for row in result} != appearance_set:
        raise SourceCanonicalDiffError("canonical player proposal does not match authoritative appearance population")
    return result


def _leeds_substitutions(source_bundle: Mapping[str, Any]) -> list[dict[str, Any]]:
    staged = _mapping(source_bundle.get("staged_events"), "source_bundle.staged_events")
    events = staged.get("events")
    if not isinstance(events, list):
        raise SourceCanonicalDiffError("staged event list is missing")
    result = []
    for raw in events:
        if not isinstance(raw, Mapping):
            continue
        if raw.get("event_kind") != "substitution" or raw.get("team_side") != "LEEDS":
            continue
        result.append(
            {
                "player_out": _integer(raw.get("provider_player_id"), "substitution player out"),
                "player_in": _integer(
                    raw.get("provider_secondary_player_id"), "substitution player in"
                ),
                "minute_base": _integer(raw.get("minute_base"), "substitution minute"),
                "stoppage_minute": _integer(
                    raw.get("stoppage_minute"), "substitution stoppage minute"
                ),
            }
        )
    return result


def _incident_rows(raw_payloads: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    incidents = _mapping(raw_payloads.get("incidents"), "raw_payloads.incidents")
    rows = incidents.get("incidents")
    if not isinstance(rows, list):
        raise SourceCanonicalDiffError("raw incidents population is missing")
    return [row for row in rows if isinstance(row, Mapping)]


def _goal_shots(raw_payloads: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    shotmap = _mapping(raw_payloads.get("shotmap"), "raw_payloads.shotmap")
    rows = shotmap.get("shotmap")
    if not isinstance(rows, list):
        raise SourceCanonicalDiffError("raw shotmap population is missing")
    return [
        row for row in rows
        if isinstance(row, Mapping) and row.get("shotType") == "goal"
    ]


def _matching_goal_shot(
    *, incident: Mapping[str, Any], shots: list[Mapping[str, Any]]
) -> Mapping[str, Any]:
    player_id = _source_player_id(incident)
    minute = _integer(incident.get("time"), "goal incident time")
    matches = [
        shot for shot in shots
        if shot.get("isHome") == incident.get("isHome")
        and isinstance(shot.get("player"), Mapping)
        and shot["player"].get("id") == player_id
        and shot.get("time") == minute
    ]
    if len(matches) != 1:
        raise SourceCanonicalDiffError(
            f"expected one goal shot for provider player {player_id} at {minute}; found {len(matches)}"
        )
    return matches[0]


def _goal_rows(
    *,
    raw_payloads: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    leeds_is_home = source_bundle.get("leeds_is_home")
    if not isinstance(leeds_is_home, bool):
        raise SourceCanonicalDiffError("source bundle has no Leeds home/away identity")
    reconciliation = _mapping(source_bundle.get("reconciliation"), "source reconciliation")
    goals = _mapping(reconciliation.get("goals"), "goal reconciliation")
    chronology = goals.get("chronology")
    if not isinstance(chronology, list):
        raise SourceCanonicalDiffError("reconciled goal chronology is missing")
    final = _mapping(goals.get("final_score"), "goal final score")
    semantics = derive_leeds_goal_semantics(
        chronology=[row for row in chronology if isinstance(row, Mapping)],
        leeds_is_home=leeds_is_home,
        final_home_score=_integer(final.get("home"), "final home score"),
        final_away_score=_integer(final.get("away"), "final away score"),
    )
    semantic_by_key = {
        (row["provider_player_id"], row["minute"], row["added_time"]): row
        for row in semantics
    }

    incidents = [
        row for row in _incident_rows(raw_payloads) if row.get("incidentType") == "goal"
    ]
    incidents.sort(
        key=lambda row: (
            _integer(row.get("time"), "goal time"),
            row.get("addedTime") if isinstance(row.get("addedTime"), int) else 0,
        )
    )
    shots = _goal_shots(raw_payloads)
    leeds_rows: list[dict[str, Any]] = []
    opposition_rows: list[dict[str, Any]] = []

    for incident in incidents:
        minute = _integer(incident.get("time"), "goal time")
        added = incident.get("addedTime") if isinstance(incident.get("addedTime"), int) else 0
        if added == 999:
            added = 0
        provider_player_id = _source_player_id(incident)
        shot = _matching_goal_shot(incident=incident, shots=shots)
        base = {
            "provider_event_id": _integer(shot.get("id"), "goal shot provider ID"),
            "provider_player_id": provider_player_id,
            "scorer_name": _source_player_name(incident),
            "minute_raw": _minute_raw(minute, added),
            "minute_normalised": minute,
        }
        if incident.get("isHome") == leeds_is_home:
            semantic = semantic_by_key.get((provider_player_id, minute, added))
            if semantic is None:
                raise SourceCanonicalDiffError("Leeds goal has no derived canonical semantics")
            assist = incident.get("assist1") or incident.get("assist")
            assist_provider_id = None
            assist_name = None
            if isinstance(assist, Mapping):
                assist_provider_id = _integer(assist.get("id"), "goal assist provider ID")
                assist_name = _text(assist.get("name"), "goal assist name")
            leeds_rows.append(
                {
                    **base,
                    "assist_provider_player_id": assist_provider_id,
                    "assist_name": assist_name,
                    "is_own_goal": str(incident.get("incidentClass") or "").casefold()
                    in {"owngoal", "own goal"},
                    "goal_type": None,
                    "location": None,
                    "body_part": None,
                    "goal_state": semantic["goal_state"],
                    "game_state": semantic["game_state"],
                }
            )
        else:
            opposition_rows.append(base)

    return leeds_rows, opposition_rows


def build_source_canonical_diff(
    *,
    raw_payloads: Mapping[str, Any],
    source_bundle: Mapping[str, Any],
    evidence_bundle: Mapping[str, Any],
    identity_package: Mapping[str, Any],
    canonical_context: Mapping[str, Any],
    leeds_team_provider_id: int,
) -> dict[str, Any]:
    """Return one source-derived, enriched, zero-write canonical diff proposal."""
    if source_bundle.get("status") != "PASS":
        raise SourceCanonicalDiffError("source bundle is not PASS")
    if evidence_bundle.get("status") != "PASS":
        raise SourceCanonicalDiffError("evidence bundle is not PASS")

    event = _mapping(raw_payloads.get("event"), "raw_payloads.event")
    event_id = _integer(event.get("id"), "event.id")
    if source_bundle.get("sofascore_event_id") != event_id:
        raise SourceCanonicalDiffError("source bundle event ID does not match raw event")

    leeds_is_home = source_bundle.get("leeds_is_home")
    if not isinstance(leeds_is_home, bool):
        raise SourceCanonicalDiffError("source bundle has no Leeds side")
    leeds_side = "home" if leeds_is_home else "away"
    opposition_side = "away" if leeds_is_home else "home"

    validations = _mapping(evidence_bundle.get("validations"), "evidence validations")
    attendance = _mapping(validations.get("attendance"), "attendance validation")
    formations = _mapping(validations.get("formations"), "formation validation")
    managers = _mapping(validations.get("managers"), "manager validation")
    captains = _mapping(validations.get("captains"), "captain validation")
    leeds_formation = _mapping(formations.get(leeds_side), "Leeds formation")

    event_dt = _event_datetime(event)
    home_score = _mapping(event.get("homeScore"), "event.homeScore")
    away_score = _mapping(event.get("awayScore"), "event.awayScore")
    round_info = _mapping(event.get("roundInfo"), "event.roundInfo")
    leeds_players = _lineup_rows(source_bundle, leeds_side)
    leeds_goals, opposition_goals = _goal_rows(
        raw_payloads=raw_payloads,
        source_bundle=source_bundle,
    )

    fixture = {
        "event_id": event_id,
        "home_team_provider_id": _integer(
            source_bundle.get("home_team_provider_id"), "home team provider ID"
        ),
        "away_team_provider_id": _integer(
            source_bundle.get("away_team_provider_id"), "away team provider ID"
        ),
        "home_score": _integer(home_score.get("current"), "home final score"),
        "away_score": _integer(away_score.get("current"), "away final score"),
        "match_date": event_dt.date().isoformat(),
        "stadium": _venue_name(event),
        "attendance": _integer(attendance.get("attendance"), "attendance"),
        "referee": _referee_name(event),
        "kickoff_time": event_dt.strftime("%H:%M"),
        "round": str(_integer(round_info.get("round"), "round")),
        "leeds_formation": _text(leeds_formation.get("formation"), "Leeds formation"),
    }

    proposed = build_proposed_canonical_diff(
        fixture=fixture,
        identity_package=identity_package,
        leeds_team_provider_id=leeds_team_provider_id,
        leeds_manager_provider_id=_integer(
            managers.get(f"{leeds_side}_manager_provider_id"), "Leeds manager provider ID"
        ),
        leeds_captain_provider_id=_integer(
            captains.get(f"{leeds_side}_captain_provider_id"), "Leeds captain provider ID"
        ),
        leeds_players=leeds_players,
        leeds_substitutions=_leeds_substitutions(source_bundle),
        leeds_goals=leeds_goals,
        opposition_goals=opposition_goals,
        opposition_manager_provider_id=_integer(
            managers.get(f"{opposition_side}_manager_provider_id"),
            "opposition manager provider ID",
        ),
        opposition_captain_provider_id=_integer(
            captains.get(f"{opposition_side}_captain_provider_id"),
            "opposition captain provider ID",
        ),
        attendance_source=_text(attendance.get("source"), "attendance source"),
    )

    enrichment = build_canonical_match_enrichment(
        source_bundle=source_bundle,
        evidence_bundle=evidence_bundle,
        canonical_context=canonical_context,
    )
    result = merge_match_enrichment_into_canonical_diff(
        canonical_diff=proposed,
        enrichment=enrichment,
    )
    result["source_derived"] = True
    result["database_writes"] = 0
    result["promotion_performed"] = False
    return result
