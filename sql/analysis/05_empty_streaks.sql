-- 05 How long do stations stay completely empty?
-- "Gaps and islands": find runs of hours in a row where a station was empty the whole hour
-- (share_empty = 1). Trick: for consecutive hours, hour_utc minus (row number x 1 hour) gives
-- the same value, so it works as an id for each unbroken run. A missing hour breaks the run.
-- All hours count (night too), because an empty station overnight is still empty at 5am.
-- Output: each station's single longest run, top 15 stations.
with empty_hours as (

    select station_id, hour_utc
    from analytics.fct_station_hourly
    where share_empty = 1

),

islands as (

    select
        station_id,
        hour_utc,
        hour_utc - row_number() over (partition by station_id order by hour_utc) * interval '1 hour' as streak_id
    from empty_hours

),

streaks as (

    select
        station_id,
        min(hour_utc) as streak_start_utc,
        count(*)      as hours_empty
    from islands
    group by station_id, streak_id

),

longest_per_station as (

    select distinct on (station_id)
        station_id,
        streak_start_utc,
        hours_empty
    from streaks
    order by station_id, hours_empty desc, streak_start_utc

)

select
    longest.station_id,
    station.station_name,
    (longest.streak_start_utc at time zone 'UTC') at time zone 'Europe/Dublin' as streak_start_local,
    longest.hours_empty,
    round(longest.hours_empty / 24.0, 1)                                         as days_empty
from longest_per_station as longest
join analytics.dim_station as station
    on station.station_id = longest.station_id
order by longest.hours_empty desc
limit 15;