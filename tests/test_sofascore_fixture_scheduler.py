from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


def _load(name: str):
    path = SCRIPTS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_load("sofascore_readonly_collector")
scheduler = _load("sofascore_fixture_scheduler")


def _utc(hour: int, minute: int, second: int = 0) -> datetime:
    return datetime(2026, 9, 12, hour, minute, second, tzinfo=timezone.utc)


def test_first_full_time_check_is_kickoff_plus_115_minutes():
    kickoff = _utc(15, 0)
    assert scheduler._next_ft_check(kickoff, _utc(16, 0)) == _utc(16, 55)


def test_full_time_rechecks_follow_ten_minute_slots():
    kickoff = _utc(15, 0)
    assert scheduler._next_ft_check(kickoff, _utc(16, 56)) == _utc(17, 5)
    assert scheduler._next_ft_check(kickoff, _utc(17, 6)) == _utc(17, 15)
    assert scheduler._next_ft_check(kickoff, _utc(17, 16)) == _utc(17, 25)


def test_exact_check_time_advances_to_next_slot_after_first_check():
    kickoff = _utc(15, 0)
    assert scheduler._next_ft_check(kickoff, _utc(16, 55)) == _utc(16, 55)
    assert scheduler._next_ft_check(kickoff, _utc(17, 5)) == _utc(17, 15)


def test_provider_kickoff_change_moves_full_time_window_automatically():
    original = {"startTimestamp": int(_utc(15, 0).timestamp())}
    moved = {"startTimestamp": int(_utc(16, 30).timestamp())}

    original_kickoff = scheduler._event_datetime(original)
    moved_kickoff = scheduler._event_datetime(moved)
    assert original_kickoff is not None and moved_kickoff is not None

    assert scheduler._next_ft_check(original_kickoff, _utc(12, 0)) == _utc(16, 55)
    assert scheduler._next_ft_check(moved_kickoff, _utc(12, 0)) == _utc(18, 25)


def test_event_without_provider_timestamp_has_no_scheduler_datetime():
    assert scheduler._event_datetime({}) is None
