"""Download Met Éireann hourly weather (Dublin Airport) and load it into PostgreSQL.

Met Éireann publishes one file per station containing the full history,
updated monthly. So every run downloads the latest file and replaces the whole
table with it (a full refresh), inside one transaction: the table is never half loaded.
"""

import csv
import logging
import sys
from pathlib import Path

import psycopg
import requests
from dotenv import load_dotenv

WEATHER_FILE = Path(__file__).resolve().parents[1] / "data" / "weather" / "hly532.csv"
WEATHER_URL = "https://clidata.met.ie/cli/climate_data/showdata.php?action=download&file=hly532.csv"

# The file's own header, and the names we load it under ("ind" appears five times).
FILE_HEADER = [
    "date", "ind", "rain", "ind", "temp", "ind", "wetb", "dewpt", "vappr", "rhum", "msl",
    "ind", "wdsp", "ind", "wddir", "ww", "w", "sun", "vis", "clht", "clamt",
]
COLUMNS = [
    "date", "rain_ind", "rain", "temp_ind", "temp", "wetb_ind", "wetb", "dewpt", "vappr", "rhum", "msl",
    "wdsp_ind", "wdsp", "wddir_ind", "wddir", "ww", "w", "sun", "vis", "clht", "clamt",
]

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("weather_loader")

COPY_SQL = f"COPY raw.weather_hourly ({', '.join(COLUMNS)}, source_file) FROM STDIN"


def download_weather():
    """Download the latest file to a .part file first, then replace the old copy."""
    WEATHER_FILE.parent.mkdir(parents=True, exist_ok=True)
    part = WEATHER_FILE.with_suffix(".csv.part")
    with requests.get(WEATHER_URL, stream=True, timeout=60) as response:
        response.raise_for_status()
        with part.open("wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
    part.replace(WEATHER_FILE)
    log.info("Downloaded %s (%.1f MB)", WEATHER_FILE.name, WEATHER_FILE.stat().st_size / 1024 / 1024)


def read_rows(path):
    """Skip the description lines at the top of the file, check the header, then yield data rows."""
    with path.open(newline="", encoding="utf-8") as f:
        for line in f:
            if line.startswith("date,"):
                header = line.strip().split(",")
                if header != FILE_HEADER:
                    raise ValueError(f"unexpected columns: {header}")
                break
        else:
            raise ValueError("header line starting with 'date,' not found")

        for row in csv.reader(f):
            if len(row) != len(FILE_HEADER):
                raise ValueError(f"row has {len(row)} fields, expected {len(FILE_HEADER)}: {row}")
            yield row


def main():
    try:
        download_weather()
    except requests.RequestException as error:
        log.error("Download failed: %s", error)
        return 1

    # psycopg reads PGHOST, PGPORT, PGDATABASE, PGUSER and PGPASSWORD from the environment
    try:
        conn = psycopg.connect(autocommit=True)
    except psycopg.OperationalError as error:
        log.error("Could not connect to PostgreSQL: %s", error)
        return 1

    with conn:
        try:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM raw.weather_hourly")
                    rows = 0
                    with cur.copy(COPY_SQL) as copy:
                        for row in read_rows(WEATHER_FILE):
                            copy.write_row(row + [WEATHER_FILE.name])
                            rows += 1
        except (ValueError, psycopg.Error) as error:
            log.error("Load failed, table left as it was: %s", error)
            return 1

    log.info("Loaded %s: %d rows", WEATHER_FILE.name, rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
