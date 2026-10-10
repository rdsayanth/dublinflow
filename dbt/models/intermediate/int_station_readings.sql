-- All station readings in one place: Smart Dublin history (May 2024 to June 2026)
-- plus the live feed collected since 2026-10-04. One row per station per reading.
-- Live check (2026-10-10): GBFS last_reported is over an hour old for 96% of rows,
-- yet bike counts still change between snapshots (29% of the time), so we use the
-- snapshot time and ignore last_reported.

select
    snapshot_at_utc,
    station_id,
    bikes_available,
    docks_available,
    is_installed,
    is_renting,
    'history' as data_source
from {{ ref('stg_dublinbikes_history') }}

union all

select
    snapshot_at_utc,
    station_id,
    bikes_available,
    docks_available,
    is_installed,
    is_renting,
    'live' as data_source
from {{ ref('stg_gbfs_station_status') }}