from __future__ import annotations

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
_load("sofascore_capture_loader")
_load("sofascore_promotion_gate")
_load("sofascore_ingestion_run_package")
_load("sofascore_staged_events")
_load("sofascore_source_derived_dry_run")
_load("sofascore_evidence_validations")
_load("sofascore_source_driven_ingestion_package")
runner = _load("sofascore_capture_to_package")


def test_capture_runner_passes_only_verified_raw_payloads_to_orchestrator(tmp_path, monkeypatch):
    verified_raw = {"event": {"id": 16363258}}
    capture_result = {
        "status": "PASS",
        "sofascore_event_id": 16363258,
        "raw_payloads": verified_raw,
        "manifest_sha256": "manifest-hash",
        "verified_payload_sha256": {"event": "event-hash"},
        "unavailable_payloads": {"graph": {"status": "unavailable"}},
        "database_writes": 0,
        "canonical_lufc_ids_assigned": False,
        "promotion_performed": False,
    }
    captured = {}

    monkeypatch.setattr(runner, "load_verified_capture", lambda capture_dir: capture_result)

    def fake_build(**kwargs):
        captured.update(kwargs)
        return {
            "status": "BLOCKED",
            "package": {
                "database_writes": 0,
                "canonical_promotion_performed": False,
            },
            "database_writes": 0,
            "canonical_promotion_performed": False,
        }

    monkeypatch.setattr(runner, "build_fully_evidence_driven_ingestion_package", fake_build)

    result = runner.build_package_from_capture(
        capture_dir=tmp_path,
        run_id="brighton-capture-run",
        importer_git_sha="72f65d197de31a167d71e3c9912bc0f1b8f7d4f5",
        leeds_team_provider_id=34,
        identity_package={"match": {"provider_id": 16363258, "canonical_id": 4857}},
        identity_mapping_validation={"status": "RESOLVED"},
        canonical_diff={"status": "BLOCKED", "database_writes": 0},
        secondary_evidence={"attendance": {"value": 31661, "source": "BBC Sport"}},
    )

    assert captured["raw_payloads"] is verified_raw
    assert captured["leeds_team_provider_id"] == 34
    assert result["status"] == "BLOCKED"
    assert result["capture_verification"]["manifest_sha256"] == "manifest-hash"
    assert result["capture_verification"]["verified_payload_sha256"] == {"event": "event-hash"}
    assert result["capture_verification"]["unavailable_payloads"]["graph"]["status"] == "unavailable"
    assert result["database_writes"] == 0
    assert result["canonical_promotion_performed"] is False


def test_capture_runner_refuses_orchestrator_write_claim(tmp_path, monkeypatch):
    monkeypatch.setattr(
        runner,
        "load_verified_capture",
        lambda capture_dir: {
            "status": "PASS",
            "sofascore_event_id": 1,
            "raw_payloads": {"event": {"id": 1}},
            "manifest_sha256": "m",
            "verified_payload_sha256": {"event": "e"},
            "unavailable_payloads": {},
        },
    )
    monkeypatch.setattr(
        runner,
        "build_fully_evidence_driven_ingestion_package",
        lambda **kwargs: {
            "status": "READY_FOR_PROMOTION",
            "package": {"database_writes": 1, "canonical_promotion_performed": False},
            "database_writes": 1,
            "canonical_promotion_performed": False,
        },
    )

    with pytest.raises(runner.CaptureToPackageError, match="reports database writes"):
        runner.build_package_from_capture(
            capture_dir=tmp_path,
            run_id="unsafe",
            importer_git_sha="abc",
            leeds_team_provider_id=34,
            identity_package={"match": {"provider_id": 1, "canonical_id": 1}},
            identity_mapping_validation={"status": "RESOLVED"},
            canonical_diff={"status": "PASS", "database_writes": 0},
        )


def test_cli_writes_zero_write_package_json(tmp_path, monkeypatch, capsys):
    identity_path = tmp_path / "identity.json"
    identity_validation_path = tmp_path / "identity-validation.json"
    diff_path = tmp_path / "diff.json"
    output_path = tmp_path / "out" / "package.json"
    identity_path.write_text(json.dumps({"match": {"provider_id": 16363258, "canonical_id": 4857}}), encoding="utf-8")
    identity_validation_path.write_text(json.dumps({"status": "RESOLVED"}), encoding="utf-8")
    diff_path.write_text(json.dumps({"status": "BLOCKED", "database_writes": 0}), encoding="utf-8")

    monkeypatch.setattr(
        runner,
        "build_package_from_capture",
        lambda **kwargs: {
            "status": "BLOCKED",
            "capture_verification": {"status": "PASS"},
            "ingestion": {"status": "BLOCKED"},
            "database_writes": 0,
            "canonical_promotion_performed": False,
        },
    )

    code = runner.main([
        "--capture-dir", str(tmp_path / "capture"),
        "--run-id", "brighton-cli",
        "--importer-git-sha", "abc123",
        "--identity-package", str(identity_path),
        "--identity-validation", str(identity_validation_path),
        "--canonical-diff", str(diff_path),
        "--output", str(output_path),
    ])

    assert code == 0
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert written["database_writes"] == 0
    assert written["canonical_promotion_performed"] is False
    assert "ZERO-WRITE INGESTION PACKAGE: BLOCKED" in capsys.readouterr().out
