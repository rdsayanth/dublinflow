"""Load Smart Dublin historical Dublin Bikes CSVs into PostgreSQL.

Reads every CSV in data/historical/ and copies it into raw.dublinbikes_history.
Each file loads in one transaction and is recorded in raw.history_file_load,
so a file is either fully loaded or not at all, and re-runs skip loaded files.
"""

import csv
import logging
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

HISTORY_DIR = Path(__file__).resolve().parents[1] / "data" / "historical"
EXPECTED_HEADER = [
    "system_id", "last_reported", "station_id", "num_bikes_available", "num_docks_available",
    "is_installed", "is_renting", "is_returning", "name", "short_name", "address",
    "lat", "lon", "region_id", "capacity",
]

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("history_loader")

COPY_SQL = f"COPY raw.dublinbikes_history ({', '.join(EXPECTED_HEADER)}, source_file) FROM STDIN"


def load_file(conn, path):
    """Copy one CSV into the raw table and record it. Returns the row count."""
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        if header != EXPECTED_HEADER:
            raise ValueError(f"unexpected columns: {header}")

        rows = 0
        with conn.transaction():
            with conn.cursor() as cur:
                with cur.copy(COPY_SQL) as copy:
                    for row in reader:
                        copy.write_row(row + [path.name])
                        rows += 1
                cur.execute(
                    "INSERT INTO raw.history_file_load (source_file, row_count) VALUES (%s, %s)",
                    (path.name, rows),
                )
    return rows


def main():
    files = sorted(HISTORY_DIR.glob("*.csv"))
    if not files:
        log.error("No CSV files found in %s", HISTORY_DIR)
        return 1

    # psycopg reads PGHOST, PGPORT, PGDATABASE, PGUSER and PGPASSWORD from the environment
    try:
        conn = psycopg.connect(autocommit=True)
    except psycopg.OperationalError as error:
        log.error("Could not connect to PostgreSQL: %s", error)
        return 1

    with conn:
        loaded = {row[0] for row in conn.execute("SELECT source_file FROM raw.history_file_load")}
        new_files = [path for path in files if path.name not in loaded]
        log.info("%d files in folder, %d already loaded, %d new", len(files), len(files) - len(new_files), len(new_files))

        failed = 0
        for path in new_files:
            try:
                rows = load_file(conn, path)
            except (ValueError, csv.Error, psycopg.Error) as error:
                log.error("Skipping %s: %s", path.name, error)
                failed += 1
                continue
            log.info("Loaded %s: %d rows", path.name, rows)

    log.info("Done: %d new files loaded, %d failed", len(new_files) - failed, failed)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
