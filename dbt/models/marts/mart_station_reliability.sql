-- One row per station: how reliable it is to find a bike or a free dock during service hours.
-- Reliability Score = 100 x (1 - share of time empty - share of time full).
-- Each service hour counts equally (average of the hourly shares).
-- Out-of-service time (0 bikes and 0 docks) is left out of the score and reported separately.

with service_hours as (

    select fact.*
    from {{ ref('fct_station_hourly') }} as fact
    join {{ ref('dim_hour') }} as hour
        on hour.hour_utc = fact.hour_utc
    where hour.is_service_hour

),

per_station as (

    select
        station_id,
        count(*)                  as service_hours,
        count(share_empty)        as in_service_hours,      -- count() skips NULL = hours fully out of service
        avg(share_empty)          as share_empty,
        avg(share_full)           as share_full,
        avg(share_out_of_service) as share_out_of_service
    from service_hours
    group by station_id

)

select
    per_station.station_id,
    station.station_name,
    station.capacity,
    per_station.service_hours,
    per_station.in_service_hours,
    round(100 * per_station.share_out_of_service, 1)                     as pct_out_of_service,
    round(100 * per_station.share_empty, 1)                              as pct_empty,
    round(100 * per_station.share_full, 1)                               as pct_full,
    round(100 * (1 - per_station.share_empty - per_station.share_full), 1) as reliability_score,
    rank() over (
        order by per_station.share_empty + per_station.share_full
    )                                                                    as reliability_rank   -- 1 = most reliable
from per_station
join {{ ref('dim_station') }} as station
    on station.station_id = per_station.station_id