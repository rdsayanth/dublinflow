"""Collect Dublin Bikes GBFS snapshots and save them as raw JSON files.
 
Each feed is saved exactly as received to:
    data/raw/<feed>/<YYYY-MM-DD>/<feed>_<YYYYMMDDTHHMMSSZ>.json
File names use the feed's own last_updated time (UTC), so fetching the same
snapshot twice overwrites one file instead of creating a duplicate.
"""
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
 
import requests
 
BASE_URL = "https://api.cyclocity.fr/contracts/dublin/gbfs/v2"
FEEDS = ["station_status", "station_information"]
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
MAX_ATTEMPTS = 3
TIMEOUT_SECONDS = 30
 
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("collector")
 
 
def fetch_feed(feed):
    """Download one feed, retrying if the request fails."""
    url = f"{BASE_URL}/{feed}.json"
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(url, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            return response
        except requests.RequestException as error:
            log.warning("%s: attempt %d of %d failed: %s", feed, attempt, MAX_ATTEMPTS, error)
            if attempt == MAX_ATTEMPTS:
                raise
            time.sleep(5 * attempt)  # wait 5s, then 10s, before trying again
 
 
def save_raw(feed, response):
    """Check the response looks like a real snapshot, then save it unchanged."""
    payload = response.json()
    stations = payload["data"]["stations"]
    if not stations:
        raise ValueError(f"{feed}: feed returned 0 stations")
 
    feed_time = datetime.fromtimestamp(payload["last_updated"], tz=timezone.utc)
    out_dir = RAW_DIR / feed / feed_time.strftime("%Y-%m-%d")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{feed}_{feed_time:%Y%m%dT%H%M%SZ}.json"
    out_file.write_text(response.text, encoding="utf-8")
    log.info("%s: saved %d stations to %s", feed, len(stations), out_file)
 
 
def main():
    failed = []
    for feed in FEEDS:
        try:
            save_raw(feed, fetch_feed(feed))
        except (requests.RequestException, ValueError, KeyError) as error:
            log.error("%s: FAILED: %s", feed, error)
            failed.append(feed)
    if failed:
        sys.exit(1)  # a non-zero exit code tells GitHub Actions the run failed
 
 
if __name__ == "__main__":
    main()
 

