#!/usr/bin/env python3
"""Fail-closed appearance-population validation for SofaScore ingestion.

A named bench is squad evidence, not appearance evidence. For either Leeds or an
opponent, the only valid appearance population is the starting XI plus players
proven to have entered the pitch.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class AppearancePopulation:
    starters: frozenset[int]
    used_substitutes: frozenset[int]
    unused_bench: frozenset[int]

    @property
    def appearances(self) -> frozenset[int]:
        return self.starters | self.used_substitutes


def validate_appearance_population(
    *,
    side: str,
    starter_ids: Iterable[int],
    bench_ids: Iterable[int],
    player_on_ids: Iterable[int],
) -> AppearancePopulation:
    """Return the authoritative appearance population or block on ambiguity."""
    starters = frozenset(starter_ids)
    bench = frozenset(bench_ids)
    used = frozenset(player_on_ids)

    if len(starters) != 11:
        raise ValueError(f"IMPORT BLOCKED — {side}: expected exactly 11 starters, found {len(starters)}")
    if not starters.isdisjoint(bench):
        raise ValueError(f"IMPORT BLOCKED — {side}: player appears in both starting XI and bench")
    if not used.issubset(bench):
        raise ValueError(f"IMPORT BLOCKED — {side}: player-on population is not contained in named bench")

    unused = bench - used
    appearances = starters | used
    if appearances & unused:
        raise ValueError(f"IMPORT BLOCKED — {side}: unused bench contaminated appearance population")

    return AppearancePopulation(starters=starters, used_substitutes=used, unused_bench=unused)


def validate_both_sides(*, leeds: dict, opponent: dict) -> dict[str, AppearancePopulation]:
    """Apply the identical appearance contract independently to both teams."""
    return {
        "leeds": validate_appearance_population(side="Leeds", **leeds),
        "opponent": validate_appearance_population(side="Opponent", **opponent),
    }
