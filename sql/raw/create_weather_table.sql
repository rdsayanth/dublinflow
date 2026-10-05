-- Met Éireann hourly weather for Dublin Airport (station 532), from hly532.csv.
-- Run while connected to the "dublinflow" database.

-- One row per hour, values kept as text exactly as in the file.
-- The file repeats the column name "ind" five times, so each indicator is
-- renamed after the value it describes (rain_ind, temp_ind, ...).
CREATE TABLE IF NOT EXISTS raw.weather_hourly (
    date         text,
    rain_ind     text,
    rain         text,
    temp_ind     text,
    temp         text,
    wetb_ind     text,
    wetb         text,
    dewpt        text,
    vappr        text,
    rhum         text,
    msl          text,
    wdsp_ind     text,
    wdsp         text,
    wddir_ind    text,
    wddir        text,
    ww           text,
    w            text,
    sun          text,
    vis          text,
    clht         text,
    clamt        text,
    source_file  text        NOT NULL,
    loaded_at    timestamptz NOT NULL DEFAULT now()
);
