"""Collect Dublin Bikes GBFS snapshots and save them as raw JSON files.

Each feed is saved exactly as received to:
    data/raw/<feed>/<YYYY-MM-DD>/<feed>_<YYYYMMDDTHHMMSSZ>.json
and, when AZURE_RAW_CONTAINER_SAS_URL is set, uploaded to the same path in the
Azure Blob container "raw".
File names use the feed's own last_updated time (UTC), so fetching the same
snapshot twice overwrites one file instead of creating a duplicate.
"""
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from azure.core.exceptions import AzureError
from azure.storage.blob import ContainerClient, ContentSettings
from dotenv import load_dotenv

BASE_URL = "https://api.cyclocity.fr/contracts/dublin/gbfs/v2"
FEEDS = ["station_status", "station_information"]
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
MAX_ATTEMPTS = 3
TIMEOUT_SECONDS = 30

load_dotenv()  # reads .env on your laptop; on GitHub the secret arrives as an env variable
SAS_URL = os.getenv("AZURE_RAW_CONTAINER_SAS_URL")
IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("collector")
logging.getLogger("azure").setLevel(logging.WARNING)  # hide the Azure library's per-request HTTP logs


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
    """Check the response looks like a real snapshot, then save it unchanged.

    Returns the path relative to data/raw, which is also used as the blob name.
    """
    payload = response.json()
    stations = payload["data"]["stations"]
    if not stations:
        raise ValueError(f"{feed}: feed returned 0 stations")

    feed_time = datetime.fromtimestamp(payload["last_updated"], tz=timezone.utc)
    relative_path = f"{feed}/{feed_time:%Y-%m-%d}/{feed}_{feed_time:%Y%m%dT%H%M%SZ}.json"
    out_file = RAW_DIR / relative_path
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    log.info("%s: saved %d stations to %s", feed, len(stations), out_file)
    return relative_path


def upload_raw(container, relative_path):
    """Upload one saved file to the Azure Blob container, keeping the same path."""
    data = (RAW_DIR / relative_path).read_bytes()
    container.upload_blob(
        relative_path,
        data,
        overwrite=True,
        content_settings=ContentSettings(content_type="application/json"),
    )
    log.info("uploaded to blob raw/%s", relative_path)


def main():
    if SAS_URL:
        container = ContainerClient.from_container_url(SAS_URL)
    elif IN_GITHUB_ACTIONS:
        log.error("AZURE_RAW_CONTAINER_SAS_URL is not set, so files would be lost")
        sys.exit(1)
    else:
        container = None
        log.warning("AZURE_RAW_CONTAINER_SAS_URL is not set: saving locally only")

    failed = []
    for feed in FEEDS:
        try:
            relative_path = save_raw(feed, fetch_feed(feed))
            if container:
                upload_raw(container, relative_path)
        except (requests.RequestException, ValueError, KeyError, AzureError) as error:
            log.error("%s: FAILED: %s", feed, error)
            failed.append(feed)
    if failed:
        sys.exit(1)  # a non-zero exit code tells GitHub Actions the run failed


if __name__ == "__main__":
    main()
