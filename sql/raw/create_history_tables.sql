-- Historical Dublin Bikes station data from Smart Dublin (monthly CSVs, May 2024 onwards).
-- Run while connected to the "dublinflow" database.

-- One row per station per snapshot, values kept as text exactly as in the CSV.
-- Types are cast and tested later in dbt staging.
CREATE TABLE IF NOT EXISTS raw.dublinbikes_history (
    system_id            text,
    last_reported        text,
    station_id           text,
    num_bikes_available  text,
    num_docks_available  text,
    is_installed         text,
    is_renting           text,
    is_returning         text,
    name                 text,
    short_name           text,
    address              text,
    lat                  text,
    lon                  text,
    region_id            text,
    capacity             text,
    source_file          text NOT NULL
);

-- One row per CSV file loaded, so the loader knows what to skip.
CREATE TABLE IF NOT EXISTS raw.history_file_load (
    source_file  text        PRIMARY KEY,
    row_count    integer     NOT NULL,
    loaded_at    timestamptz NOT NULL DEFAULT now()
);
