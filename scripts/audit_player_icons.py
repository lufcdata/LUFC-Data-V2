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


def fetch_players() -> list[dict]:
    query = urlencode({"select": "player_id,legacy_player_id,display_name,profile_image_url", "order": "display_name.asc"})
    req = Request(
        f"{SUPABASE_URL}/rest/v1/players?{query}",
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
    )
    with urlopen(req, timeout=30) as response:
        return json.load(response)


def main() -> None:
    players = fetch_players()
    icon_files = sorted(p.name for p in ICON_DIR.iterdir() if p.is_file() and p.suffix.lower() == ".png")
    icon_names = {name.removesuffix(" Icon.png"): name for name in icon_files if name.endswith(" Icon.png")}

    matched = []
    missing_players = []
    matched_files = set()
    for player in players:
        name = player["display_name"]
        filename = icon_names.get(name)
        if filename:
            path = f"/playericons/{filename}"
            matched.append({
                "player_id": player["player_id"],
                "legacy_player_id": player["legacy_player_id"],
                "display_name": name,
                "filename": filename,
                "profile_image_url": path,
            })
            matched_files.add(filename)
        else:
            missing_players.append({
                "player_id": player["player_id"],
                "legacy_player_id": player["legacy_player_id"],
                "display_name": name,
            })

    orphan_icons = [name for name in icon_files if name not in matched_files]
    report = {
        "players_total": len(players),
        "icon_files_total": len(icon_files),
        "matched_rows": len(matched),
        "matched_unique_names": len({m["display_name"] for m in matched}),
        "missing_rows": len(missing_players),
        "missing_unique_names": len({m["display_name"] for m in missing_players}),
        "matched": matched,
        "missing_players": missing_players,
        "orphan_icons": orphan_icons,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["players_total", "icon_files_total", "matched_rows", "matched_unique_names", "missing_rows", "missing_unique_names"]}, indent=2))
    print(f"Audit report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
