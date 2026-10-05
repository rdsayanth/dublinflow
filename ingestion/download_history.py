"""Download Smart Dublin historical Dublin Bikes station CSVs (May 2024 to June 2026).

Files go to data/historical/ (ignored by Git). Files already there are skipped.
Each download is written to a .part file first and renamed when complete,
so a broken download never looks like a finished CSV.
"""

import logging
import sys
from pathlib import Path

import requests

HISTORY_DIR = Path(__file__).resolve().parents[1] / "data" / "historical"
BASE_URL = "https://data.smartdublin.ie/dataset/33ec9fe2-4957-4e9a-ab55-c5e917c7a9ab/resource"

# Month (MMYYYY, as in the file name) -> Smart Dublin resource id.
# Taken from https://data.smartdublin.ie/dataset/dublinbikes-api on 2026-10-04.
# March and April 2024 are not published.
RESOURCES = {
    "052024": "87a171b3-82b1-4e47-9b36-75e579adf3f9",
    "062024": "022119a2-7679-4742-9b0a-c39dce0f38c1",
    "072024": "7f8ccbf8-4144-48b6-971a-02d534d164e5",
    "082024": "6c13cb05-f31e-414e-a8be-16f2d9f4e53e",
    "092024": "168f55b8-1c3d-4fd3-95b9-f92f388c772a",
    "102024": "f9182676-043d-41dc-a8d4-fe602f677a0d",
    "112024": "578d5726-8e59-4d15-84d0-bb755c530e22",
    "122024": "215455d4-6028-4035-aca6-455e48ba80f1",
    "012025": "3b10f5a3-58f0-4fa6-9210-ae950a185ab8",
    "022025": "2bac02ee-d480-48d5-bece-b3968fb74c30",
    "032025": "ef819959-8183-45d4-a0bb-8027cf8f0876",
    "042025": "ab8604b5-9fe4-4e7b-b112-6ebacdfd039d",
    "052025": "b67b71f3-311e-4206-aed1-ce0c958947c9",
    "062025": "11fd116e-760a-4237-9bcf-abbace46a32a",
    "072025": "5b5afbcc-61e0-48d0-870e-a22df2ea4793",
    "082025": "1cb1e957-3600-4cfc-abf7-6d5749108d4e",
    "092025": "921175fc-4182-4616-b981-35da50dacea1",
    "102025": "c9556189-9df4-4391-a0c4-18c3b8bc9f54",
    "112025": "e432e75f-ad0d-44ff-8e09-2a5ab88972e5",
    "122025": "89b9cc0c-e1da-4993-ba99-b64c70953d4e",
    "012026": "afff7586-654b-40e3-8c65-e76ce88a1ccc",
    "022026": "91098ee8-7ea7-4c70-b96d-face618a02b6",
    "032026": "33bbe7a6-3b30-49cf-a13d-0ef622dbedb1",
    "042026": "92857912-1a36-4c8e-bd85-d26177609dbf",
    "052026": "03dd67ef-33b0-4102-8329-42c67fdbf53e",
    "062026": "fdce169c-3164-46b3-bc71-fb8684e50ef4",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("history_download")


def download(month, resource_id):
    file_name = f"dublin-bikes_station_status_{month}.csv"
    target = HISTORY_DIR / file_name
    if target.exists():
        log.info("Already have %s", file_name)
        return

    part = target.with_suffix(".csv.part")
    url = f"{BASE_URL}/{resource_id}/download/{file_name}"
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with part.open("wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
    part.rename(target)
    log.info("Downloaded %s (%.1f MB)", file_name, target.stat().st_size / 1024 / 1024)


def main():
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    failed = 0
    for month, resource_id in RESOURCES.items():
        try:
            download(month, resource_id)
        except requests.RequestException as error:
            log.error("Failed %s: %s", month, error)
            failed += 1
    log.info("Done: %d failed", failed)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
