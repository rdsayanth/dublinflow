-- One row per Dublin Bikes station seen in the history.
-- Name, location and capacity come from each station's most recent reading.

with history as (

    select * from {{ ref('stg_dublinbikes_history') }}

),

latest as (

    select distinct on (station_id)
        station_id,
        station_name,
        latitude,
        longitude,
        capacity,
        is_installed
    from history
    order by station_id, snapshot_at_utc desc

),

seen as (

    select
        station_id,
        min(snapshot_at_utc) as first_seen_utc,
        max(snapshot_at_utc) as last_seen_utc
    from history
    group by station_id

)

select
    latest.station_id,
    latest.station_name,
    latest.latitude,
    latest.longitude,
    latest.capacity,
    latest.is_installed      as is_installed_at_last_reading,
    seen.first_seen_utc,
    seen.last_seen_utc

from latest
join seen using (station_id)