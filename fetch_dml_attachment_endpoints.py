import json
import os
import time
from pathlib import Path
import requests

LEAGUE_ID = 60018
CURRENT_ROUND = 24
OUT = Path("dml_data")
OUT.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (DML League Hub data importer)",
    "Accept": "application/json,text/plain,*/*",
    "Referer": "https://fantasy.nrl.com/draft/league/60018/",
}

def get_json(url, filename):
    print(f"[GET] {url}")
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    path = OUT / filename
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] {path} ({len(r.content):,} bytes)")
    return data

def main():
    # Player master data: names, IDs and other player metadata.
    get_json(
        "https://tds-nrl-data.s3-ap-southeast-2.amazonaws.com/data/nrl/players.json",
        "players.json"
    )

    # Current transaction feed.
    get_json(
        f"https://fantasy.nrl.com/nrl_draft/api/teams_draft/trades?league_id={LEAGUE_ID}",
        "trades.json"
    )

    # Historical/current league ladder snapshots.
    for rnd in range(1, CURRENT_ROUND + 1):
        get_json(
            f"https://fantasy.nrl.com/nrl_draft/api/leagues_draft/ladder?league_id={LEAGUE_ID}&round={rnd}",
            f"ladder_round_{rnd:02d}.json"
        )
        time.sleep(0.15)

    print("\nComplete: player master + trades + ladder R1-R24 saved in ./dml_data/")
    print("Next imports can use these files to build the DML League Hub database.")

if __name__ == "__main__":
    main()
