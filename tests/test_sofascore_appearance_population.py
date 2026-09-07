from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sofascore_appearance_population.py"
spec = importlib.util.spec_from_file_location("appearance_population", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
validate = module.validate_appearance_population
validate_both = module.validate_both_sides


def test_unused_bench_never_counts_as_appearance():
    result = validate(
        side="Leeds",
        starter_ids=range(1, 12),
        bench_ids=range(12, 21),
        player_on_ids=(12, 13, 14, 15),
    )
    assert result.appearances == frozenset(range(1, 16))
    assert result.unused_bench == frozenset(range(16, 21))
    assert len(result.appearances) == 15


def test_player_on_must_be_from_named_bench():
    with pytest.raises(ValueError, match="IMPORT BLOCKED"):
        validate(side="Leeds", starter_ids=range(1, 12), bench_ids=(12, 13), player_on_ids=(99,))


def test_exactly_eleven_starters_required():
    with pytest.raises(ValueError, match="expected exactly 11 starters"):
        validate(side="Opponent", starter_ids=range(1, 11), bench_ids=(12, 13), player_on_ids=(12,))


def test_same_contract_applies_to_leeds_and_opponent():
    populations = validate_both(
        leeds={"starter_ids": range(1, 12), "bench_ids": range(12, 21), "player_on_ids": (12, 13, 14, 15)},
        opponent={"starter_ids": range(101, 112), "bench_ids": range(112, 121), "player_on_ids": (112, 113, 114)},
    )
    assert len(populations["leeds"].appearances) == 15
    assert len(populations["opponent"].appearances) == 14
    assert populations["leeds"].appearances.isdisjoint(populations["leeds"].unused_bench)
    assert populations["opponent"].appearances.isdisjoint(populations["opponent"].unused_bench)
