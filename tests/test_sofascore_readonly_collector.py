from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sofascore_readonly_collector.py"
SPEC = importlib.util.spec_from_file_location("sofascore_readonly_collector", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
collector = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = collector
SPEC.loader.exec_module(collector)


def _event(*, status_type: str = "finished", opponent: str = "Brighton & Hove Albion"):
    description = "Finished" if status_type == "finished" else "Not started"
    return {
        "id": 123456789,
        "startTimestamp": int(
            datetime(2026, 9, 5, 14, 0, tzinfo=timezone.utc).timestamp()
        ),
        "status": {"type": status_type, "description": description},
        "homeTeam": {"id": 30, "name": opponent},
        "awayTeam": {"id": 34, "name": "Leeds United"},
        "tournament": {"name": "Premier League"},
    }


def test_brighton_target_matches_completed_leeds_fixture():
    target = collector.FixtureTarget(
        date="2026-09-05",
        opponent="Brighton",
        competition="Premier League",
    )

    assert collector._matches_target(_event(), 34, target) is True


def test_scheduled_fixture_is_not_ingestable():
    target = collector.FixtureTarget("2026-09-05", "Brighton", "Premier League")

    assert collector._matches_target(_event(status_type="notstarted"), 34, target) is False


def test_wrong_opponent_is_not_ingestable():
    target = collector.FixtureTarget("2026-09-05", "Brighton", "Premier League")

    assert collector._matches_target(_event(opponent="Brentford"), 34, target) is False


def test_payload_family_includes_shotmap_and_average_positions():
    urls = collector._payload_urls(16363258)
    assert urls["shotmap"] == "https://www.sofascore.com/api/v1/event/16363258/shotmap"
    assert urls["average_positions"] == "https://www.sofascore.com/api/v1/event/16363258/average-positions"


def test_premier_league_event_derives_total_standings_url():
    event = {
        "tournament": {
            "name": "Premier League",
            "uniqueTournament": {"id": 17},
        },
        "season": {"id": 96668},
    }
    assert collector._standings_url_from_event(event) == (
        "https://www.sofascore.com/api/v1/unique-tournament/17/season/96668/standings/total"
    )


def test_non_league_event_does_not_query_standings():
    event = {
        "tournament": {
            "name": "FA Cup",
            "uniqueTournament": {"id": 19},
        },
        "season": {"id": 96668},
    }
    assert collector._standings_url_from_event(event) is None


def test_league_capture_adds_standings_to_manifest(tmp_path, monkeypatch):
    event_url = "https://www.sofascore.com/api/v1/event/16363258"
    standings_url = (
        "https://www.sofascore.com/api/v1/unique-tournament/17/season/96668/standings/total"
    )
    payloads = {
        event_url: {
            "id": 16363258,
            "tournament": {
                "name": "Premier League",
                "uniqueTournament": {"id": 17},
            },
            "season": {"id": 96668},
        },
        standings_url: {
            "standings": [
                {"rows": [{"team": {"id": 34}, "position": 9, "matches": 3, "points": 5}]}
            ]
        },
    }

    def fake_get_json(url: str, timeout: int = 20):
        return payloads.get(url, {})

    monkeypatch.setattr(collector, "_get_json", fake_get_json)
    manifest_path = collector.collect_payload_family(16363258, tmp_path, 0)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["payloads"]["standings"]["status"] == "captured"
    assert manifest["payloads"]["standings"]["url"] == standings_url
    assert (tmp_path / "16363258" / "standings.json").exists()


def test_provider_ids_remain_external_in_manifest_shape(tmp_path, monkeypatch):
    payloads = {
        "https://www.sofascore.com/api/v1/event/123456789": {"event": {"id": 123456789}},
    }

    def fake_get_json(url: str, timeout: int = 20):
        return payloads.get(url, {})

    monkeypatch.setattr(collector, "_get_json", fake_get_json)
    manifest_path = collector.collect_payload_family(123456789, tmp_path, 0)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["provider"] == "sofascore"
    assert manifest["sofascore_event_id"] == 123456789
    assert manifest["database_writes"] == 0
    assert manifest["canonical_lufc_ids_assigned"] is False
    assert "shotmap" in manifest["payloads"]
    assert "average_positions" in manifest["payloads"]
