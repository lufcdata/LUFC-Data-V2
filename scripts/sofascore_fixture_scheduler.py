#!/usr/bin/env python3
"""Fixture-aware, read-only Leeds scheduler for SofaScore ingestion.

Discovers Leeds' next fixture directly from SofaScore so broadcaster moves to date
or kick-off are picked up from the provider rather than a stale local calendar.
The match-day policy begins full-time status checks at kick-off + 115 minutes and
then permits another check every 10 minutes until SofaScore reports finished.
No canonical database writes are performed here.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sofascore_readonly_collector import (
    BASE_URL,
    DEFAULT_LEEDS_SOFASCORE_TEAM_ID,
    _competition_name,
    _get_json,
    _is_finished,
    _team_name,
)

STATE_PATH = Path("source_data/sofascore/scheduler_state.json")
COLLECTOR = Path(__file__).with_name("sofascore_readonly_collector.py")
FIRST_FT_CHECK_MINUTES = 115
FT_RECHECK_MINUTES = 10


def _leeds_event(event: dict[str, Any], team_id: int) -> bool:
    home = event.get("homeTeam") if isinstance(event.get("homeTeam"), dict) else {}
    away = event.get("awayTeam") if isinstance(event.get("awayTeam"), dict) else {}
    return team_id in {home.get("id"), away.get("id")}


def _opponent(event: dict[str, Any], team_id: int) -> str:
    home = event.get("homeTeam") if isinstance(event.get("homeTeam"), dict) else {}
    return _team_name(event, "awayTeam") if home.get("id") == team_id else _team_name(event, "homeTeam")


def _event_datetime(event: dict[str, Any]) -> datetime | None:
    ts = event.get("startTimestamp")
    return datetime.fromtimestamp(ts, timezone.utc) if isinstance(ts, (int, float)) else None


def _events(team_id: int, direction: str, pages: int = 3) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for page in range(pages):
        payload = _get_json(f"{BASE_URL}/team/{team_id}/events/{direction}/{page}")
        rows = payload.get("events")
        if not isinstance(rows, list):
            continue
        found.extend(e for e in rows if isinstance(e, dict) and _leeds_event(e, team_id))
        if not payload.get("hasNextPage"):
            break
    return found


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"captured_event_ids": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"captured_event_ids": []}
    return data if isinstance(data, dict) else {"captured_event_ids": []}


def _save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _next_ft_check(kickoff: datetime, now: datetime) -> datetime:
    first = kickoff + timedelta(minutes=FIRST_FT_CHECK_MINUTES)
    if now <= first:
        return first
    elapsed = (now - first).total_seconds()
    intervals = int(elapsed // (FT_RECHECK_MINUTES * 60)) + 1
    return first + timedelta(minutes=intervals * FT_RECHECK_MINUTES)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--team-id", type=int, default=DEFAULT_LEEDS_SOFASCORE_TEAM_ID)
    parser.add_argument("--state", type=Path, default=STATE_PATH)
    parser.add_argument("--no-collect", action="store_true")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    future = [e for e in _events(args.team_id, "next") if (_event_datetime(e) or now) >= now]
    future.sort(key=lambda e: _event_datetime(e) or datetime.max.replace(tzinfo=timezone.utc))
    next_event = future[0] if future else None

    state = _load_state(args.state)
    captured = {int(x) for x in state.get("captured_event_ids", []) if str(x).isdigit()}
    recent = _events(args.team_id, "last")
    completed = [e for e in recent if _is_finished(e) and isinstance(e.get("id"), int)]
    completed.sort(key=lambda e: _event_datetime(e) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    uncaptured = [e for e in completed if int(e["id"]) not in captured]

    if next_event:
        dt = _event_datetime(next_event)
        print("NEXT_FIXTURE", next_event.get("id"), dt.isoformat() if dt else "UNKNOWN", _opponent(next_event, args.team_id), _competition_name(next_event))
        if dt:
            print("FIRST_FT_CHECK", (dt + timedelta(minutes=FIRST_FT_CHECK_MINUTES)).isoformat())
    else:
        print("NEXT_FIXTURE NONE")

    # A started fixture may have moved from the provider's next feed to its last feed
    # before it is finished. Surface the next useful polling time without treating time
    # itself as proof of full-time.
    unfinished_recent = [e for e in recent if not _is_finished(e) and isinstance(e.get("id"), int)]
    unfinished_recent.sort(key=lambda e: _event_datetime(e) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    if unfinished_recent:
        live = unfinished_recent[0]
        kickoff = _event_datetime(live)
        if kickoff and kickoff <= now:
            print("MATCH_DAY_NEXT_CHECK", live["id"], _next_ft_check(kickoff, now).isoformat())

    if not uncaptured:
        print("CAPTURE_ACTION NONE")
        return 0

    event = uncaptured[0]
    event_id = int(event["id"])
    dt = _event_datetime(event)
    if dt is None:
        print(f"BLOCKED event {event_id}: missing startTimestamp", file=sys.stderr)
        return 1
    print("FINISHED_UNCAPTURED", event_id, dt.isoformat(), _opponent(event, args.team_id), _competition_name(event))
    if args.no_collect:
        return 0

    command = [
        sys.executable, str(COLLECTOR),
        "--date", dt.date().isoformat(),
        "--opponent", _opponent(event, args.team_id),
        "--competition", _competition_name(event),
        "--sofascore-leeds-team-id", str(args.team_id),
    ]
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        print(f"BLOCKED collector failed for SofaScore event {event_id}", file=sys.stderr)
        return result.returncode

    captured.add(event_id)
    state["captured_event_ids"] = sorted(captured)
    state["last_successful_capture_utc"] = datetime.now(timezone.utc).isoformat()
    state["last_successful_event_id"] = event_id
    _save_state(args.state, state)
    print(f"CAPTURED event {event_id}; canonical database writes: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
