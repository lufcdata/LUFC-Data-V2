from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sofascore_promotion_gate.py"
SPEC = importlib.util.spec_from_file_location("sofascore_promotion_gate", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gate
SPEC.loader.exec_module(gate)


def _all_passed() -> dict:
    return {name: {"status": "PASS"} for name in gate.REQUIRED_VALIDATION_GATES}


def test_brighton_dry_run_is_blocked_until_backup_and_rollback_exist():
    result = gate.evaluate_promotion_gate(_all_passed())

    assert result["status"] == "BLOCKED"
    assert result["passed_validation_count"] == len(gate.REQUIRED_VALIDATION_GATES)
    assert result["backup"] == "REQUIRED"
    assert result["rollback_manifest"] == "REQUIRED"
    assert result["database_writes"] == 0
    assert result["promotion_performed"] is False


def test_verified_backup_without_rollback_manifest_is_still_blocked():
    result = gate.evaluate_promotion_gate(
        _all_passed(),
        backup={"status": "VERIFIED"},
    )

    assert result["status"] == "BLOCKED"
    assert result["backup"] == "VERIFIED"
    assert result["rollback_manifest"] == "REQUIRED"


def test_one_failed_validation_blocks_even_with_backup_and_rollback():
    validations = _all_passed()
    validations["identity_mapping"] = {"status": "BLOCKED"}

    result = gate.evaluate_promotion_gate(
        validations,
        backup={"status": "VERIFIED"},
        rollback_manifest={"status": "READY"},
    )

    assert result["status"] == "BLOCKED"
    assert "validation not passed: identity_mapping (BLOCKED)" in result["blockers"]


def test_missing_validation_blocks_fail_closed():
    validations = _all_passed()
    validations.pop("attendance")

    result = gate.evaluate_promotion_gate(
        validations,
        backup={"status": "VERIFIED"},
        rollback_manifest={"status": "READY"},
    )

    assert result["status"] == "BLOCKED"
    assert "missing validation: attendance" in result["blockers"]


def test_not_applicable_is_an_explicit_pass_state_for_conditional_fields():
    validations = _all_passed()
    validations["league_position"] = {"status": "NOT_APPLICABLE"}

    result = gate.evaluate_promotion_gate(
        validations,
        backup={"status": "VERIFIED"},
        rollback_manifest={"status": "READY"},
    )

    assert result["status"] == "READY_FOR_PROMOTION"
    assert result["blocker_count"] == 0
    assert result["database_writes"] == 0


def test_all_validations_plus_verified_backup_and_rollback_can_become_ready():
    result = gate.evaluate_promotion_gate(
        _all_passed(),
        backup={"status": "VERIFIED"},
        rollback_manifest={"status": "READY"},
    )

    assert result["status"] == "READY_FOR_PROMOTION"
    assert result["passed_validation_count"] == len(gate.REQUIRED_VALIDATION_GATES)
    assert result["blocker_count"] == 0
    assert result["database_writes"] == 0
    assert result["promotion_performed"] is False


def test_require_ready_raises_for_blocked_proposal():
    result = gate.evaluate_promotion_gate(_all_passed())

    with pytest.raises(gate.PromotionGateError, match="promotion blocked"):
        gate.require_ready_for_promotion(result)
