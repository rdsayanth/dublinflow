# Data dictionary

All the tables in the DublinFlow warehouse (PostgreSQL), layer by layer. All times are UTC unless a column name says `local`. The column lists match the dbt models in `dbt/models/`.

| Layer | Schema | Built by | Stored as |
|---|---|---|---|
| Raw | `raw` | Python loaders in `ingestion/` | tables, all text, exactly as received |
| Staging | `analytics` | dbt (`stg_*`) | views: typed and renamed, one source each |
| Intermediate | `analytics` | dbt (`int_*`) | view: history and live joined together |
| Marts | `analytics` | dbt (`dim_*`, `fct_*`, `mart_*`) | tables: the star schema Power BI reads |

Power BI uses the four mart tables: `fct_station_hourly`, `dim_station`, `dim_hour` and `mart_station_reliability`.

## Marts (star schema)

### fct_station_hourly

The fact table. **One row per station per hour.** It combines the 2 years of history and the live feed. Only readings where the station is installed are used. If a station has no reading in an hour, that hour is left out (no forward-fill).

| Column | Type | Meaning |
|---|---|---|
| `station_id` | integer | Station number. Links to `dim_station`. |
| `hour_utc` | timestamp | Start of the hour, UTC. Links to `dim_hour`. |
| `data_source` | text | `history` (Smart Dublin files) or `live` (the feed collected since 2026-10-04). |
| `readings` | integer | Number of readings in the hour. History has one every 5 minutes, live one every 10 minutes. |
| `avg_bikes_available` | numeric | Average bikes available in the hour. |
| `min_bikes_available` | integer | Lowest bike count in the hour. |
| `share_empty` | numeric 0 to 1 | Share of in-service readings with 0 bikes. NULL if the whole hour was out of service. |
| `share_full` | numeric 0 to 1 | Share of in-service readings with 0 free docks. NULL if the whole hour was out of service. |
| `share_out_of_service` | numeric 0 to 1 | Share of readings with 0 bikes and 0 free docks at the same time, which means the docks were out of service. |
| `share_not_renting` | numeric 0 to 1 | Share of readings where the feed said the station was not renting. |

Key: `station_id` + `hour_utc` (tested unique).

### dim_station

**One row per station** (115 stations). Name, location and capacity come from each station's most recent reading in the history.

| Column | Type | Meaning |
|---|---|---|
| `station_id` | integer | Station number. Primary key. |
| `station_name` | text | Station name. |
| `latitude` | numeric | Latitude. |
| `longitude` | numeric | Longitude. |
| `capacity` | integer | Number of docks. |
| `is_installed_at_last_reading` | boolean | Whether the station was installed at its last reading. |
| `first_seen_utc` | timestamp | First reading in the history. |
| `last_seen_utc` | timestamp | Last reading in the history. |

### dim_hour

**One row per hour** from 1 May 2024 to now, with Irish local time and the weather. Weather is Met Éireann hourly data from Dublin Airport. Met Éireann stamps each hour's rain at the end of that hour, so the hour starting at 08:00 takes the weather row stamped 09:00. Weather is NULL until Met Éireann publishes that month.

| Column | Type | Meaning |
|---|---|---|
| `hour_utc` | timestamp | Start of the hour, UTC. Primary key. |
| `hour_local` | timestamp | Same hour in Irish local time (Europe/Dublin, handles summer time). |
| `date_local` | date | Local date. |
| `hour_of_day_local` | integer | Local hour, 0 to 23. |
| `day_of_week` | integer | 1 = Monday to 7 = Sunday. |
| `day_name` | text | Mon, Tue and so on. |
| `is_weekend` | boolean | True on Saturday and Sunday. |
| `is_service_hour` | boolean | True for local hours 05:00 to 23:59. Bikes can be rented 05:00 to 00:30. The Reliability Score only counts these hours. |
| `rain_mm` | numeric | Rain in the hour, mm. |
| `is_rain_hour` | boolean | True if `rain_mm` > 0. |
| `temp_c` | numeric | Air temperature, °C. |
| `wind_speed_kt` | integer | Mean wind speed, knots. |
| `humidity_pct` | integer | Relative humidity, %. |
| `sunshine_hours` | numeric | Sunshine in the hour, hours (0 to 1). |

### mart_station_reliability

**One row per station**: its Reliability Score and rank. Only service hours are counted (`dim_hour.is_service_hour`), and each hour counts equally.

| Column | Type | Meaning |
|---|---|---|
| `station_id` | integer | Station number. Primary key. |
| `station_name` | text | Station name (from `dim_station`). |
| `capacity` | integer | Number of docks. |
| `service_hours` | integer | Service hours with at least one reading. |
| `in_service_hours` | integer | Service hours that were not fully out of service. |
| `pct_out_of_service` | numeric | % of service time with the docks out of service. Not part of the score. |
| `pct_empty` | numeric | % of in-service time with 0 bikes. |
| `pct_full` | numeric | % of in-service time with 0 free docks. |
| `reliability_score` | numeric | 100 × (1 − share empty − share full). 100 means never empty or full. |
| `reliability_rank` | integer | 1 = most reliable. Ties share a rank. |

## Intermediate

### int_station_readings

**One row per station per reading**: the history (May 2024 to June 2026) and the live feed (since 2026-10-04) stacked together. The live feed's `last_reported` field is ignored because it is often hours old even when counts change. The snapshot time is used instead.

Columns: `snapshot_at_utc`, `station_id`, `bikes_available`, `docks_available`, `is_installed`, `is_renting`, `data_source` (`history` or `live`).

## Staging

| Model | Source | Grain | Main columns |
|---|---|---|---|
| `stg_dublinbikes_history` | `raw.dublinbikes_history` | station × 5-minute snapshot | `snapshot_at_utc`, `station_id`, `bikes_available`, `docks_available`, `is_installed`, `is_renting`, `is_returning`, `station_name`, `latitude`, `longitude`, `capacity`, `source_file` |
| `stg_gbfs_station_status` | `raw.gbfs_snapshot` | station × 10-minute snapshot | `snapshot_at_utc`, `station_id`, `bikes_available`, `docks_available`, `is_installed`, `is_renting`, `is_returning`, `station_last_reported_utc` (not used) |
| `stg_weather_hourly` | `raw.weather_hourly` | hour | `observed_at_utc`, `rain_mm`, `temp_c`, `humidity_pct`, `pressure_hpa`, `wind_speed_kt`, `wind_dir_deg`, `sunshine_hours`, `visibility_m`, `rain_quality_code` |

## Raw

| Table | Loaded from | One row per |
|---|---|---|
| `raw.gbfs_snapshot` | JSON files the collector saves to Azure Blob Storage every 10 minutes (GBFS live feed) | JSON file. Key: `blob_path`. |
| `raw.dublinbikes_history` | Smart Dublin monthly CSV files, May 2024 to June 2026 | station per 5-minute snapshot |
| `raw.weather_hourly` | Met Éireann hourly CSV, Dublin Airport (station 532) | hour |

## Key rules

- **Times:** everything is stored in UTC. Local time only appears in `dim_hour`.
- **Out of service:** a reading with 0 bikes and 0 free docks counts as out of service, not as empty or full.
- **No forward-fill:** missing hours stay missing rather than being filled in.
- **Tests:** dbt runs 33 data tests on every build (unique keys, not null, relationships and the score range 0 to 100). See [data_quality.md](data_quality.md).

Weather data: Copyright Met Éireann. Source: www.met.ie. Licence: CC BY 4.0.
