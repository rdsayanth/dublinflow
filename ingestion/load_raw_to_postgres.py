"""Load raw GBFS JSON files from Azure Blob Storage into PostgreSQL.

Each blob becomes one row in raw.gbfs_snapshot. Files already in the table
are skipped, so the script is safe to run again at any time.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone

import psycopg
from azure.core.exceptions import AzureError
from azure.storage.blob import ContainerClient
from dotenv import load_dotenv
from psycopg.types.json import Jsonb

FEEDS = {"station_status", "station_information"}

load_dotenv()
SAS_URL = os.getenv("AZURE_RAW_CONTAINER_READ_SAS_URL")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("loader")
logging.getLogger("azure").setLevel(logging.WARNING)

INSERT_SQL = """
    INSERT INTO raw.gbfs_snapshot (blob_path, feed, feed_last_updated, payload)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (blob_path) DO NOTHING
"""


def main():
    if not SAS_URL:
        log.error("AZURE_RAW_CONTAINER_READ_SAS_URL is not set in .env")
        return 1

    container = ContainerClient.from_container_url(SAS_URL)

    # psycopg reads PGHOST, PGPORT, PGDATABASE, PGUSER and PGPASSWORD from the environment
    try:
        conn = psycopg.connect()
    except psycopg.OperationalError as error:
        log.error("Could not connect to PostgreSQL: %s", error)
        return 1

    with conn:
        loaded = {row[0] for row in conn.execute("SELECT blob_path FROM raw.gbfs_snapshot")}
        conn.commit()

        try:
            all_blobs = [blob.name for blob in container.list_blobs()]
        except AzureError as error:
            log.error("Could not list files in Azure: %s", error)
            return 1

        new_blobs = sorted(name for name in all_blobs if name not in loaded)
        log.info("%d files in Azure, %d already loaded, %d new", len(all_blobs), len(all_blobs) - len(new_blobs), len(new_blobs))

        inserted = failed = 0
        for name in new_blobs:
            feed = name.split("/")[0]
            if feed not in FEEDS:
                log.warning("Skipping %s: unknown feed", name)
                continue
            try:
                payload = json.loads(container.download_blob(name).readall())
                feed_time = datetime.fromtimestamp(payload["last_updated"], tz=timezone.utc)
            except (AzureError, ValueError, KeyError) as error:
                log.error("Skipping %s: %s", name, error)
                failed += 1
                continue

            conn.execute(INSERT_SQL, (name, feed, feed_time, Jsonb(payload)))
            conn.commit()  # commit each file, so progress is kept if the run stops halfway
            inserted += 1

    log.info("Loaded %d new files, %d failed", inserted, failed)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
