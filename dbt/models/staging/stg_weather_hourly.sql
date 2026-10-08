-- Met Éireann hourly weather at Dublin Airport (station 532).
-- One row per hour. Text columns cast to proper types; blank values become NULL.

with source as (

    select * from {{ source('raw', 'weather_hourly') }}

)

select
    date::timestamp                          as observed_at_utc,  -- naive timestamp, always UTC
    nullif(trim(rain), '')::numeric(5, 1)    as rain_mm,
    nullif(trim(temp), '')::numeric(4, 1)    as temp_c,
    nullif(trim(rhum), '')::integer          as humidity_pct,
    nullif(trim(msl), '')::numeric(5, 1)     as pressure_hpa,
    nullif(trim(wdsp), '')::integer          as wind_speed_kt,
    nullif(trim(wddir), '')::integer         as wind_dir_deg,
    nullif(trim(sun), '')::numeric(3, 1)     as sunshine_hours,
    nullif(trim(vis), '')::integer           as visibility_m,
    nullif(trim(rain_ind), '')::integer      as rain_quality_code  -- 111 = "investigation required"

from source