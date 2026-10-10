-- One row per station per hour (UTC), from the history and the live feed.
-- Gap check (2026-10-08): stations report every 5 to 15 minutes (99.9% of gaps),
-- so each station-hour has several readings and no forward-fill is needed at this grain.
-- Hours with no reading for a station are left out rather than invented.
-- Station capacity, name and location live in dim_station.

with readings as (

    select * from {{ ref('int_station_readings') }}
    where is_installed

)

select
    station_id,
    date_trunc('hour', snapshot_at_utc)          as hour_utc,
    max(data_source)                             as data_source,
    count(*)                                     as readings,
    round(avg(bikes_available), 1)               as avg_bikes_available,
    min(bikes_available)                         as min_bikes_available,
    round(avg((bikes_available = 0)::int), 3)    as share_empty,
    round(avg((docks_available = 0)::int), 3)    as share_full,
    round(avg((not is_renting)::int), 3)         as share_not_renting

from readings
group by station_id, date_trunc('hour', snapshot_at_utc)