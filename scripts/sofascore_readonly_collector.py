#!/usr/bin/env python3
"""Read-only SofaScore collector for LUFC ingestion research.

This script deliberately has no Supabase/database imports and performs no canonical
writes. It discovers a completed Leeds fixture from SofaScore's team event feed,
then captures the raw event payload family to ignored local source_data storage.

External SofaScore IDs are always labelled as provider IDs. They must never be
used as LUFC canonical match/player/team/manager IDs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

BASE_URL = "https://www.sofascore.com/api/v1"
DEFAULT_LEEDS_SOFASCORE_TEAM_ID = 34
DEFAULT_OUTPUT_ROOT = Path("source_data/sofascore")
USER_AGENT = "LUFC-Data-V2-SofaScore-Research/1.0"


class CollectorError(RuntimeError):
    """Raised when source collection cannot be completed safely."""


@dataclass(frozen=True)
class FixtureTarget:
    date: str
    opponent: str
    competition: str | None = None


def _get_json(url: str, timeout: int = 20) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:  # nosec B310: fixed HTTPS source
            status = getattr(response, "status", 200)
            if status != 200:
                raise CollectorError(f"GET {url} returned HTTP {status}")
            raw = response.read()
    except HTTPError as exc:
        raise CollectorError(f"GET {url} returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise CollectorError(f"GET {url} failed: {exc.reason}") from exc

    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CollectorError(f"GET {url} did not return valid UTF-8 JSON") from exc

    if not isinstance(parsed, dict):
        raise CollectorError(f"GET {url} returned a non-object JSON payload")
    return parsed


def _event_date_utc(event: dict[str, Any]) -> str | None:
    timestamp = event.get("startTimestamp")
    if not isinstance(timestamp, (int, float)):
        return None
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()


def _team_name(event: dict[str, Any], side: str) -> str:
    team = event.get(side)
    if not isinstance(team, dict):
        return ""
    return str(team.get("name") or "")


def _competition_name(event: dict[str, Any]) -> str:
    tournament = event.get("tournament")
    if not isinstance(tournament, dict):
        return ""
    return str(tournament.get("name") or "")


def _is_finished(event: dict[str, Any]) -> bool:
    status = event.get("status")
    if not isinstance(status, dict):
        return False
    status_type = str(status.get("type") or "").lower()
    description = str(status.get("description") or "").lower()
    return status_type == "finished" or description in {
        "finished",
        "after extra time",
        "after penalties",
    }


def _matches_target(
    event: dict[str, Any],
    sofascore_leeds_team_id: int,
    target: FixtureTarget,
) -> bool:
    if not _is_finished(event):
        return False
    if _event_date_utc(event) != target.date:
        return False

    home = event.get("homeTeam") if isinstance(event.get("homeTeam"), dict) else {}
    away = event.get("awayTeam") if isinstance(event.get("awayTeam"), dict) else {}
    home_id = home.get("id")
    away_id = away.get("id")
    if sofascore_leeds_team_id not in {home_id, away_id}:
        return False

    opponent_team = away if home_id == sofascore_leeds_team_id else home
    opponent_name = str(opponent_team.get("name") or "")
    if target.opponent.casefold() not in opponent_name.casefold():
        return False

    if target.competition:
        if target.competition.casefold() not in _competition_name(event).casefold():
            return False

    return True


def discover_event(
    sofascore_leeds_team_id: int,
    target: FixtureTarget,
    max_pages: int,
    delay_seconds: float,
) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []

    for page in range(max_pages):
        url = f"{BASE_URL}/team/{sofascore_leeds_team_id}/events/last/{page}"
        payload = _get_json(url)
        events = payload.get("events")
        if not isinstance(events, list):
            raise CollectorError(f"Missing events[] in {url}")

        for event in events:
            if isinstance(event, dict) and _matches_target(
                event, sofascore_leeds_team_id, target
            ):
                matches.append(event)

        if matches:
            break
        if not payload.get("hasNextPage"):
            break
        if delay_seconds > 0:
            time.sleep(delay_seconds)

    if not matches:
        raise CollectorError(
            "No completed SofaScore fixture matched the requested date/opponent/competition."
        )
    if len(matches) != 1:
        ids = [match.get("id") for match in matches]
        raise CollectorError(f"Ambiguous SofaScore fixture match; provider event IDs: {ids}")

    event = matches[0]
    if not isinstance(event.get("id"), int):
        raise CollectorError("Matched SofaScore fixture has no numeric provider event ID")
    return event


def _payload_urls(sofascore_event_id: int) -> dict[str, str]:
    base = f"{BASE_URL}/event/{sofascore_event_id}"
    return {
        "event": base,
        "lineups": f"{base}/lineups",
        "incidents": f"{base}/incidents",
        "managers": f"{base}/managers",
        "statistics": f"{base}/statistics",
        "graph": f"{base}/graph",
    }


def _stable_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _write_payload(path: Path, payload: dict[str, Any]) -> str:
    raw = _stable_json_bytes(payload)
    digest = hashlib.sha256(raw).hexdigest()
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return digest


def collect_payload_family(
    sofascore_event_id: int,
    output_root: Path,
    delay_seconds: float,
) -> Path:
    capture_dir = output_root / str(sofascore_event_id)
    capture_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "provider": "sofascore",
        "sofascore_event_id": sofascore_event_id,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "database_writes": 0,
        "canonical_lufc_ids_assigned": False,
        "payloads": {},
    }

    for index, (name, url) in enumerate(_payload_urls(sofascore_event_id).items()):
        try:
            payload = _get_json(url)
        except CollectorError as exc:
            manifest["payloads"][name] = {
                "url": url,
                "status": "unavailable",
                "error": str(exc),
            }
        else:
            filename = f"{name}.json"
            sha256 = _write_payload(capture_dir / filename, payload)
            manifest["payloads"][name] = {
                "url": url,
                "status": "captured",
                "file": filename,
                "sha256": sha256,
            }

        if delay_seconds > 0 and index < len(_payload_urls(sofascore_event_id)) - 1:
            time.sleep(delay_seconds)

    manifest_path = capture_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover and capture a completed Leeds SofaScore fixture without DB writes."
    )
    parser.add_argument("--date", required=True, help="UTC fixture date, YYYY-MM-DD")
    parser.add_argument("--opponent", required=True, help="Opponent name or unique substring")
    parser.add_argument("--competition", help="Optional competition name or unique substring")
    parser.add_argument(
        "--sofascore-leeds-team-id",
        type=int,
        default=DEFAULT_LEEDS_SOFASCORE_TEAM_ID,
        help="Provider-owned SofaScore Leeds team ID; never an LUFC club_id",
    )
    parser.add_argument("--max-pages", type=int, default=8)
    parser.add_argument("--delay", type=float, default=0.25)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    target = FixtureTarget(args.date, args.opponent, args.competition)

    try:
        datetime.strptime(args.date, "%Y-%m-%d")
        event = discover_event(
            sofascore_leeds_team_id=args.sofascore_leeds_team_id,
            target=target,
            max_pages=args.max_pages,
            delay_seconds=args.delay,
        )
        sofascore_event_id = int(event["id"])
        manifest_path = collect_payload_family(
            sofascore_event_id=sofascore_event_id,
            output_root=args.output_root,
            delay_seconds=args.delay,
        )
    except (CollectorError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1

    print("READ-ONLY SOFASCORE CAPTURE COMPLETE")
    print(f"SofaScore event ID: {sofascore_event_id}")
    print(f"Fixture: {_team_name(event, 'homeTeam')} v {_team_name(event, 'awayTeam')}")
    print(f"Competition: {_competition_name(event)}")
    print(f"UTC date: {_event_date_utc(event)}")
    print(f"Manifest: {manifest_path}")
    print("Supabase/database writes: 0")
    print("LUFC canonical IDs assigned: no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
