-- Live Dublin Bikes feed (GBFS station_status), saved by the collector every 10 minutes
-- since 2026-10-04. Each raw row is one JSON file; this model unpacks it to
-- one row per station per snapshot.

with snapshots as (

    select
        feed_last_updated,
        payload
    from {{ source('raw', 'gbfs_snapshot') }}
    where feed = 'station_status'

)

select
    snapshot.feed_last_updated at time zone 'UTC'                 as snapshot_at_utc,  -- naive UTC, like the history
    (station ->> 'station_id')::integer                          as station_id,
    (station ->> 'num_bikes_available')::integer                 as bikes_available,
    (station ->> 'num_docks_available')::integer                 as docks_available,
    (station ->> 'is_installed')::boolean                        as is_installed,
    (station ->> 'is_renting')::boolean                          as is_renting,
    (station ->> 'is_returning')::boolean                        as is_returning,
    to_timestamp((station ->> 'last_reported')::bigint)
        at time zone 'UTC'                                        as station_last_reported_utc

from snapshots as snapshot
cross join lateral jsonb_array_elements(snapshot.payload -> 'data' -> 'stations') as station