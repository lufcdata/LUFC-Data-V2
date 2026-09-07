from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


def _load(name: str):
    path = SCRIPTS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_load("sofascore_dry_run_contract")
loader = _load("sofascore_capture_loader")


def _canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha(value):
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _write_capture(root: Path, *, competition: str = "Premier League", include_standings: bool = True):
    event = {
        "id": 16363258,
        "tournament": {"name": competition},
    }
    payloads = {
        "event": event,
        "lineups": {"confirmed": True},
        "incidents": {"incidents": []},
        "managers": {"homeManager": {"id": 1}, "awayManager": {"id": 2}},
        "statistics": {"statistics": []},
        "average_positions": {"substitutions": []},
        "shotmap": {"shotmap": []},
    }
    if include_standings:
        payloads["standings"] = {"standings": []}

    entries = {}
    for name, payload in payloads.items():
        filename = f"{name}.json"
        (root / filename).write_text(json.dumps(payload), encoding="utf-8")
        entries[name] = {
            "status": "captured",
            "file": filename,
            "sha256": _sha(payload),
        }

    manifest = {
        "provider": "sofascore",
        "sofascore_event_id": 16363258,
        "database_writes": 0,
        "canonical_lufc_ids_assigned": False,
        "payloads": entries,
    }
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return payloads


def test_verified_league_capture_loads_all_required_payloads(tmp_path):
    _write_capture(tmp_path)
    result = loader.load_verified_capture(tmp_path)

    assert result["status"] == "PASS"
    assert result["sofascore_event_id"] == 16363258
    assert set(loader.MANDATORY_CAPTURE_PAYLOADS).issubset(result["raw_payloads"])
    assert "standings" in result["raw_payloads"]
    assert result["verified_payload_sha256"]["event"]
    assert result["manifest_sha256"]
    assert result["database_writes"] == 0
    assert result["canonical_lufc_ids_assigned"] is False
    assert result["promotion_performed"] is False


def test_capture_loader_rejects_payload_changed_after_manifest(tmp_path):
    _write_capture(tmp_path)
    shotmap_path = tmp_path / "shotmap.json"
    shotmap_path.write_text(json.dumps({"shotmap": [{"id": 999}]}), encoding="utf-8")

    with pytest.raises(loader.CaptureLoaderError, match="hash mismatch: shotmap"):
        loader.load_verified_capture(tmp_path)


def test_league_capture_requires_post_match_standings(tmp_path):
    _write_capture(tmp_path, include_standings=False)
    with pytest.raises(loader.CaptureLoaderError, match="missing captured post-match standings"):
        loader.load_verified_capture(tmp_path)


def test_explicit_non_league_capture_does_not_require_standings(tmp_path):
    _write_capture(tmp_path, competition="FA Cup", include_standings=False)
    result = loader.load_verified_capture(tmp_path)
    assert result["status"] == "PASS"
    assert "standings" not in result["raw_payloads"]


def test_manifest_cannot_escape_capture_directory(tmp_path):
    _write_capture(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["payloads"]["shotmap"]["file"] = "../shotmap.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(loader.CaptureLoaderError, match="unsafe captured payload filename"):
        loader.load_verified_capture(tmp_path)
