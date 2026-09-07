#!/usr/bin/env python3
"""Derive LUFC canonical goal-state semantics from a reconciled match chronology.

The canonical `goals.game_state` field describes the score state immediately BEFORE
a Leeds goal from Leeds' perspective (Level / Leading +N / Trailing -N).
`goals.goal_state` uses special labels for an equaliser or the decisive winner;
otherwise it records the chronological match-goal ordinal (1st Goal, 2nd Goal, ...).

This module is pure and zero-write. It never trusts a caller-supplied semantic label.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping


class GoalSemanticsError(RuntimeError):
    """Raised when a goal chronology cannot be interpreted deterministically."""


def _require_int(value: Any, label: str) -> int:
    if not isinstance(value, int):
        raise GoalSemanticsError(f"{label} must be an integer")
    return value


def _ordinal(value: int) -> str:
    if value <= 0:
        raise GoalSemanticsError("goal ordinal must be positive")
    last_two = value % 100
    if 11 <= last_two <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
    return f"{value}{suffix} Goal"


def _leeds_scores(home: int, away: int, *, leeds_is_home: bool) -> tuple[int, int]:
    return (home, away) if leeds_is_home else (away, home)


def _game_state(leeds_score: int, opponent_score: int) -> str:
    difference = leeds_score - opponent_score
    if difference == 0:
        return "Level"
    if difference > 0:
        return f"Leading +{difference}"
    return f"Trailing {difference}"


def derive_leeds_goal_semantics(
    *,
    chronology: Iterable[Mapping[str, Any]],
    leeds_is_home: bool,
    final_home_score: int,
    final_away_score: int,
) -> list[dict[str, Any]]:
    """Return canonical semantics for each Leeds goal in chronological order.

    The input chronology must contain every match goal in order with post-goal
    `home_score`, `away_score` and `is_home`. A decisive `Winner` is assigned only
    when a Leeds goal moves the score from level to a one-goal Leeds lead, Leeds
    ultimately win by one, and no later goal occurs. This matches the canonical
    population's use of Winner as the decisive final scoring action while avoiding
    retrospective guesses in matches with later goals.
    """
    rows = [dict(row) for row in chronology]
    if any(not isinstance(row.get("is_home"), bool) for row in rows):
        raise GoalSemanticsError("goal chronology contains an invalid scoring side")

    final_home = _require_int(final_home_score, "final home score")
    final_away = _require_int(final_away_score, "final away score")
    expected_total_goals = final_home + final_away
    if len(rows) != expected_total_goals:
        raise GoalSemanticsError(
            f"goal chronology contains {len(rows)} goals but final score contains {expected_total_goals}"
        )

    previous_home = 0
    previous_away = 0
    result: list[dict[str, Any]] = []

    for index, row in enumerate(rows, start=1):
        post_home = _require_int(row.get("home_score"), "post-goal home score")
        post_away = _require_int(row.get("away_score"), "post-goal away score")
        delta = (post_home - previous_home, post_away - previous_away)
        if delta not in {(1, 0), (0, 1)}:
            raise GoalSemanticsError(
                f"invalid goal transition {previous_home}-{previous_away} -> {post_home}-{post_away}"
            )
        scorer_is_home = row["is_home"]
        if scorer_is_home != (delta == (1, 0)):
            raise GoalSemanticsError("goal scoring side disagrees with score transition")

        leeds_scored = scorer_is_home == leeds_is_home
        pre_leeds, pre_opponent = _leeds_scores(
            previous_home, previous_away, leeds_is_home=leeds_is_home
        )
        post_leeds, post_opponent = _leeds_scores(
            post_home, post_away, leeds_is_home=leeds_is_home
        )

        if leeds_scored:
            game_state = _game_state(pre_leeds, pre_opponent)
            makes_level = post_leeds == post_opponent
            final_leeds, final_opponent = _leeds_scores(
                final_home, final_away, leeds_is_home=leeds_is_home
            )
            decisive_winner = (
                pre_leeds == pre_opponent
                and post_leeds == post_opponent + 1
                and final_leeds == final_opponent + 1
                and index == len(rows)
            )
            if decisive_winner:
                goal_state = "Winner"
            elif makes_level:
                goal_state = "Equaliser"
            else:
                goal_state = _ordinal(index)

            result.append(
                {
                    "match_goal_number": index,
                    "provider_player_id": row.get("sofascore_player_id"),
                    "minute": row.get("time"),
                    "added_time": row.get("added_time", 0),
                    "game_state": game_state,
                    "goal_state": goal_state,
                    "pre_goal_score": {"leeds": pre_leeds, "opponent": pre_opponent},
                    "post_goal_score": {"leeds": post_leeds, "opponent": post_opponent},
                }
            )

        previous_home, previous_away = post_home, post_away

    if (previous_home, previous_away) != (final_home, final_away):
        raise GoalSemanticsError("goal chronology does not end at the final score")

    return result
