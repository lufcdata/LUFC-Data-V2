from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sofascore_dry_run_contract.py"
SPEC = importlib.util.spec_from_file_location("sofascore_dry_run_contract_attendance_policy", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
contract = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = contract
SPEC.loader.exec_module(contract)


def test_verified_not_published_attendance_is_non_blocking_null():
    result = contract.attendance_candidate(
        None,
        secondary_source="BBC Sport",
        secondary_check_status="NOT_PUBLISHED",
    )

    assert result == {
        "status": "NOT_PUBLISHED",
        "attendance": None,
        "source": "BBC Sport",
        "blocking": False,
    }


def test_missing_attendance_without_completed_secondary_check_is_unresolved_and_blocking():
    result = contract.attendance_candidate(None)

    assert result == {
        "status": "UNRESOLVED",
        "attendance": None,
        "source": None,
        "blocking": True,
    }


def test_failed_secondary_check_cannot_masquerade_as_not_published():
    result = contract.attendance_candidate(
        None,
        secondary_source="BBC Sport",
        secondary_check_status="CHECK_FAILED",
    )

    assert result["status"] == "UNRESOLVED"
    assert result["attendance"] is None
    assert result["source"] == "BBC Sport"
    assert result["blocking"] is True


def test_not_published_requires_source_attribution():
    with pytest.raises(contract.ContractError, match="no source attribution"):
        contract.attendance_candidate(None, secondary_check_status="NOT_PUBLISHED")


def test_unknown_secondary_check_status_fails_closed():
    with pytest.raises(contract.ContractError, match="unknown secondary attendance check status"):
        contract.attendance_candidate(
            None,
            secondary_source="BBC Sport",
            secondary_check_status="MAYBE",
        )
