#!/usr/bin/env python3
"""Fail-fast Database Load V1 validation for PostgreSQL/Supabase."""
from __future__ import annotations
import argparse
import os

EXPECTED_COUNTS = {
    "matches": 4856,
    "players": 902,
    "manager_spells": 57,
    "goals": 7282,
    "player_matches": 58527,
}


def scalar(cur, query: str, params=()):
    cur.execute(query, params)
    return cur.fetchone()[0]


def require(name: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")
    print(f"PASS {name}: {actual}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    args = parser.parse_args()
    if not args.database_url:
        raise SystemExit("DATABASE_URL or --database-url is required")
    try:
        import psycopg
    except ImportError as exc:
        raise SystemExit("Install psycopg[binary] to validate PostgreSQL") from exc

    with psycopg.connect(args.database_url) as conn, conn.cursor() as cur:
        for table, expected in EXPECTED_COUNTS.items():
            require(table, scalar(cur, f"select count(*) from {table}"), expected)
        require("starts", scalar(cur, "select count(*) from player_matches where started"), 53416)
        require("substitute appearances", scalar(cur, "select count(*) from player_matches where substitute"), 5111)
        require("opponent own goals", scalar(cur, "select count(*) from goals where is_own_goal"), 153)

        require("duplicate player-match rows", scalar(cur, "select count(*) from (select match_id,player_id from player_matches group by 1,2 having count(*)>1) q"), 0)
        require("invalid start/sub rows", scalar(cur, "select count(*) from player_matches where started=substitute"), 0)
        require("goals without match", scalar(cur, "select count(*) from goals g left join matches m using(match_id) where m.match_id is null"), 0)

        cur.execute("select match_date,array_agg(match_id order by match_id) from matches where match_date in (date '1920-09-11',date '1920-09-25') group by match_date order by match_date")
        require("same-date regression matches", cur.fetchall(), [( __import__('datetime').date(1920,9,11), [5,6]), (__import__('datetime').date(1920,9,25), [8,9])])

        require("Ellson correction", scalar(cur, "select count(*) from goals where legacy_goal_number=10 and match_id=6"), 1)
        require("Becchio correction", scalar(cur, "select count(*) from goals g join matches m using(match_id) where g.legacy_goal_number=6046 and g.match_id=4011 and m.match_date=date '2009-05-14'"), 1)
        require("Hankin correction", scalar(cur, "select count(*) from goals g join matches m using(match_id) where g.legacy_goal_number=3868 and m.match_date=date '1978-04-26' and m.venue_type='A'"), 1)
        require("Paul Robinson identities", scalar(cur, "select count(*) from players where legacy_player_id in (518,705)"), 2)

        require("career totals rows", scalar(cur, "select count(*) from v_player_career_totals"), 902)
        require("match context rows", scalar(cur, "select count(*) from v_match_player_context"), 58527)
        require("duplicate appearance numbers", scalar(cur, "select count(*) from (select player_id,appearance_number from v_match_player_context group by 1,2 having count(*)>1) q"), 0)

    print("DATABASE LOAD V1 VALIDATION PASSED")


if __name__ == "__main__":
    main()
