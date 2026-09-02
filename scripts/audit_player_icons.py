from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / "frontend" / "public" / "playericons"
REPORT_PATH = ROOT / "player_icon_audit.json"
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://nztiaxnrwojraiwipwjj.supabase.co")
SUPABASE_KEY = os.environ["SUPABASE_PUBLISHABLE_KEY"]

TBC_PLAYERS = {
    "George Hill", "Fred Waterhouse", "Eugene O'Doherty", "George Cooper",
    "Billy Boardman", "Jimmy Clark", "John Martin", "Tom Coutts", "Ben Underwood",
    "Alan Fowler", "Bobby Abel", "Jimmy Carr", "John Trainor", "Cliff Francis",
    "Bill Parry", "Arthur Price", "Eddie Hodgkinson", "Norman Morton", "Cliff Marsh",
    "John Williams", "Ralph Harrison", "Sam McNeish", "John Finlay", "Ken Hastie",
    "Tom Wheatley", "Bobby Dawson",
}

APPROVED_FILENAMES = {
    "Albert Johanneson": "Albert Johannsenon Icon.png",
    "Alf-Inge Haaland": "Alf Inge Haaland Icon.png",
    "Andy O’Brien": "Andy O'Brien Icon.png",
    "Andy Watson": "Andrew Watson Icon.png",
    "Cameron Borthwick-Jackson": "Cameron-Borthwick Jackson Icon.png",
    "Casper Ankergren": "Casper Ankegren Icon.png",
    "Danny Cadamarteri": "Danny Cadamateri Icon.png",
    "Darren O’Dea": "Darren O'Dea Icon.png",
    "David Robertson": "David Roberton Icon.png",
    "Dominic Calvert-Lewin": "Dominic Calvert-Lewin.png",
    "Dominic Poleon": "Dom Poleon Icon.png",
    "Duncan McKenzie": "Duncan Mckenzie Icon.png",
    "Facundo Buonanotte": "Facundo Buananotte Icon.png",
    "Freddie Goodwin": "Fred Goodwin Icon.png",
    "Gabriel Gudmundsson": "Gabriel Gudmondsson Icon.png",
    "Gary McAllister": "Gary McAllister.png",
    "Geoffrey Martin": "Geoff Martin Icon.png",
    "George Stuart": "George Stewart.png",
    "Gunnar Halle": "Gunner Halle Icon.png",
    "Jay-Roy Grot": "Jay Roy Grot Icon.png",
    "Jean-Kevin Augustin": "Jean Kevin Augustin Icon.png",
    "Joël Piroe": "Joel Piroe Icon.png",
    "John O’Hare": "John O'Hare Icon.png",
    "John Thomson": "John thomson Icon.png",
    "Lee Erwin": "Lee Irwin Icon.png",
    "Malcolm Christie": "Malcomb Christie Icon.png",
    "Max Wöber": "Max Wober Icon.png",
    "Mike O’Grady": "Mike O'Grady Icon.png",
    "Niall Huggins": "Niall Hugins Icon.png",
    "Paul Robinson": "Paul Robinson GK Icon.png",
    "Rasmus Kristensen": "Rasus Kristensen Icon.png",
    "Souleymane Doukara": "Souleymane Doukara icon.png",
    "Tarik Muharemović": "Tarik Muharemovic Icon.png",
    "Teddy Lucic": "Teddy Lukic Icon.png",
    "Wally Clark": "Wally Clarke Icon.png",
    "Wayne Entwistle": "Wayne Entwhistle Icon.png",
    "Willis Edwards": "Will Edwards Icon.png",
    "Zan Benedicic": "Zan Benedidic Icon.png",
    "Jim Moore": "Jim Moore Icon .png",
    "Jimmy Allan": "Jimmy Allan Icon .png",
    "Lewie Coyle": "Lewie Coyle Icon .png",
    "Lubomir Michalik": "Lubomir Michalik Icon .png",
    "Harold Williams": "Harold Wiliams Icon.png",
    "Eric Kerfoot": "Erik Kerfoot Icon.png",
    "Ron Mollatt": "Ron Molatt Icon.png",
}


def fetch_players() -> list[dict]:
    query = urlencode({"select": "player_id,legacy_player_id,display_name,profile_image_url", "order": "legacy_player_id.asc"})
    req = Request(
        f"{SUPABASE_URL}/rest/v1/players?{query}",
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
    )
    with urlopen(req, timeout=30) as response:
        return json.load(response)


def expected_filename(name: str) -> str:
    if name in TBC_PLAYERS:
        return "Player TBC.png"
    return APPROVED_FILENAMES.get(name, f"{name} Icon.png")


def main() -> None:
    players = fetch_players()
    icon_files = {p.name for p in ICON_DIR.iterdir() if p.is_file() and p.suffix.lower() == ".png"}
    seen_names: set[str] = set()
    valid = []
    mismatches = []
    missing_files = []

    for player in players:
        name = player["display_name"]
        expected_file = expected_filename(name)
        expected_url = f"/playericons/{expected_file}"
        actual_url = player["profile_image_url"]

        if name in seen_names:
            mismatches.append({**player, "reason": "duplicate_display_name"})
            continue
        seen_names.add(name)

        if expected_file not in icon_files:
            missing_files.append({
                "player_id": player["player_id"],
                "legacy_player_id": player["legacy_player_id"],
                "display_name": name,
                "expected_filename": expected_file,
            })
            continue

        if actual_url != expected_url:
            mismatches.append({
                "player_id": player["player_id"],
                "legacy_player_id": player["legacy_player_id"],
                "display_name": name,
                "expected_url": expected_url,
                "actual_url": actual_url,
            })
            continue

        valid.append({
            "player_id": player["player_id"],
            "legacy_player_id": player["legacy_player_id"],
            "display_name": name,
            "profile_image_url": actual_url,
        })

    report = {
        "players_total": len(players),
        "unique_display_names": len(seen_names),
        "icon_files_total": len(icon_files),
        "valid_rows": len(valid),
        "tbc_players_expected": len(TBC_PLAYERS),
        "approved_filename_overrides": len(APPROVED_FILENAMES),
        "mismatch_rows": len(mismatches),
        "missing_file_rows": len(missing_files),
        "mismatches": mismatches,
        "missing_files": missing_files,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in [
        "players_total", "unique_display_names", "icon_files_total", "valid_rows",
        "tbc_players_expected", "approved_filename_overrides", "mismatch_rows", "missing_file_rows",
    ]}, indent=2))
    print(f"Audit report written to {REPORT_PATH}")

    if len(players) != 902 or len(seen_names) != 902 or mismatches or missing_files:
        raise SystemExit("Player icon audit failed")


if __name__ == "__main__":
    main()
