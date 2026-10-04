-- DublinFlow raw layer.
-- One-time setup, run while connected to the "postgres" database:
--   CREATE DATABASE dublinflow;
-- Then connect to "dublinflow" and run the rest of this file.

CREATE SCHEMA IF NOT EXISTS raw;

-- One row per raw JSON file from Azure Blob, stored untouched.
-- blob_path is the primary key, so loading the same file twice is skipped.
CREATE TABLE IF NOT EXISTS raw.gbfs_snapshot (
    blob_path          text        PRIMARY KEY,
    feed               text        NOT NULL CHECK (feed IN ('station_status', 'station_information')),
    feed_last_updated  timestamptz NOT NULL,
    payload            jsonb       NOT NULL,
    loaded_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS gbfs_snapshot_feed_time_idx
    ON raw.gbfs_snapshot (feed, feed_last_updated);