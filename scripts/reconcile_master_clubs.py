#!/usr/bin/env python3
"""Reconcile the normalized match-derived club list with the authoritative master catalogue.

The normalized importer intentionally derives opponent IDs from MATCHES.csv in first-source
occurrence order. This script preserves those IDs exactly, verifies that every match-derived
opponent exists in the 190-club master catalogue, then appends catalogue-only clubs.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MASTER = ROOT / "data" / "reference" / "master_clubs.csv"
EXPECTED_MATCH_OPPONENTS = 169
EXPECTED_MASTER_CLUBS = 190


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["club_id", "canonical_name", "display_name", "crest_url"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--normalized-dir", type=Path, required=True)
    parser.add_argument("--master-clubs", type=Path, default=DEFAULT_MASTER)
    args = parser.parse_args()

    clubs_path = args.normalized_dir / "clubs.csv"
    report_path = args.normalized_dir / "import_report.json"
    normalized = read_csv(clubs_path)
    master_rows = read_csv(args.master_clubs)
    master = [row["canonical_name"].strip() for row in master_rows if row.get("canonical_name", "").strip()]

    if len(normalized) != EXPECTED_MATCH_OPPONENTS:
        raise ValueError(f"Expected {EXPECTED_MATCH_OPPONENTS} match-derived clubs, got {len(normalized)}")
    if len(master) != EXPECTED_MASTER_CLUBS:
        raise ValueError(f"Expected {EXPECTED_MASTER_CLUBS} master clubs, got {len(master)}")
    if len(set(master)) != len(master):
        raise ValueError("Master club catalogue contains duplicate canonical names")

    normalized_names = [row["canonical_name"].strip() for row in normalized]
    missing_from_master = sorted(set(normalized_names) - set(master))
    if missing_from_master:
        raise ValueError(f"Match-derived opponents missing from master catalogue: {missing_from_master}")

    ids = [int(row["club_id"]) for row in normalized]
    if ids != list(range(1, EXPECTED_MATCH_OPPONENTS + 1)):
        raise ValueError("Match-derived club IDs are not the expected contiguous 1..169 sequence")

    out: list[dict[str, object]] = [dict(row) for row in normalized]
    existing = set(normalized_names)
    next_id = EXPECTED_MATCH_OPPONENTS + 1
    appended: list[str] = []
    for name in master:
        if name in existing:
            continue
        out.append({"club_id": next_id, "canonical_name": name, "display_name": name, "crest_url": ""})
        existing.add(name)
        appended.append(name)
        next_id += 1

    if len(out) != EXPECTED_MASTER_CLUBS:
        raise ValueError(f"Expected reconciled catalogue of {EXPECTED_MASTER_CLUBS}, got {len(out)}")
    if len(appended) != EXPECTED_MASTER_CLUBS - EXPECTED_MATCH_OPPONENTS:
        raise ValueError(f"Expected 21 appended catalogue-only clubs, got {len(appended)}")

    write_csv(clubs_path, out)

    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report.setdefault("normalized_counts", {})["clubs"] = len(out)
        report["clubs"] = {
            "match_derived_opponents": EXPECTED_MATCH_OPPONENTS,
            "master_catalogue": EXPECTED_MASTER_CLUBS,
            "catalogue_only": len(appended),
        }
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "match_derived_opponents": len(normalized),
        "master_catalogue": len(out),
        "catalogue_only_appended": len(appended),
        "appended": appended,
    }, indent=2, ensure_ascii=False))
    print("\nMASTER CLUB RECONCILIATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
