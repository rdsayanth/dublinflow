-- Smart Dublin Dublin Bikes history, May 2024 to June 2026.
-- One row per station per 5-minute snapshot, but only for stations whose
-- status was written in that snapshot (forward-fill happens in a later model).

with source as (

    select * from {{ source('raw', 'dublinbikes_history') }}

)

select
    last_reported::timestamp          as snapshot_at_utc,  -- naive timestamp, always UTC
    station_id::integer               as station_id,
    num_bikes_available::integer      as bikes_available,
    num_docks_available::integer      as docks_available,
    is_installed::boolean             as is_installed,
    is_renting::boolean               as is_renting,
    is_returning::boolean             as is_returning,
    name                              as station_name,
    lat::numeric(9, 6)                as latitude,
    lon::numeric(9, 6)                as longitude,
    capacity::integer                 as capacity,
    source_file

from source