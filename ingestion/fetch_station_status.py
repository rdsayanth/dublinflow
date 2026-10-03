from datetime import datetime, timezone
from pathlib import Path

import requests

URL = "https://api.cyclocity.fr/contracts/dublin/gbfs/v2/station_status.json"
# Repo root = the folder above ingestion/, so the script works from any folder
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "station_status"

response = requests.get(URL, timeout=30)
response.raise_for_status()
payload = response.json()

# Name the file by the feed's own time (UTC), not the time the script ran
feed_time = datetime.fromtimestamp(payload["last_updated"], tz=timezone.utc)
out_dir = RAW_DIR / feed_time.strftime("%Y-%m-%d")    # one folder per day
out_dir.mkdir(parents=True, exist_ok=True)            # create it if missing
out_file = out_dir / f"station_status_{feed_time:%Y%m%dT%H%M%SZ}.json"

# Save the response exactly as received
out_file.write_text(response.text, encoding="utf-8")

print(f"Saved {len(payload['data']['stations'])} stations to {out_file}")