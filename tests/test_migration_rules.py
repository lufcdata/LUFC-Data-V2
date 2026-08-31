from pathlib import Path
import csv


def load_corrections():
    path = Path(__file__).parents[1] / "data" / "corrections" / "migration_corrections.csv"
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_confirmed_corrections_are_present():
    rows = load_corrections()
    keys = {(r["source_locator"], r["field_name"], r["corrected_value"]) for r in rows}
    assert ("Merton Ellson | 1920-09-11 | Leicester City | Division Two", "MATCHID", "6") in keys
    assert ("Luciano Becchio | Millwall | 2009 play-off", "Date", "2009-05-14") in keys
    assert ("Luciano Becchio | Millwall | 2009-05-14", "MATCHID", "4011") in keys
    assert ("Ray Hankin | Aston Villa | 1978-04-26", "Venue", "Away") in keys
