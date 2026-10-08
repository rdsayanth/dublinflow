-- One row per hour (UTC) from May 2024 to now, with Irish local time and the weather.
-- Met Éireann stamps hourly rain at HH:00 as the total for the hour that just ended,
-- so the bike hour starting at HH:00 takes the weather row stamped HH+1:00.
-- Hours with no weather yet (Met Éireann publishes monthly) have NULL weather.

with hours as (

    select generate_series(
        timestamp '2024-05-01 00:00',
        date_trunc('hour', now() at time zone 'UTC'),
        interval '1 hour'
    ) as hour_utc

),

weather as (

    select * from {{ ref('stg_weather_hourly') }}

),

joined as (

    select
        hours.hour_utc,
        (hours.hour_utc at time zone 'UTC') at time zone 'Europe/Dublin' as hour_local,
        weather.rain_mm,
        weather.temp_c,
        weather.wind_speed_kt,
        weather.humidity_pct,
        weather.sunshine_hours
    from hours
    left join weather
        on weather.observed_at_utc = hours.hour_utc + interval '1 hour'

)

select
    hour_utc,
    hour_local,
    hour_local::date                         as date_local,
    extract(hour from hour_local)::integer   as hour_of_day_local,
    extract(isodow from hour_local)::integer as day_of_week,      -- 1 = Monday, 7 = Sunday
    to_char(hour_local, 'Dy')                as day_name,
    extract(isodow from hour_local) >= 6     as is_weekend,
    rain_mm,
    temp_c,
    wind_speed_kt,
    humidity_pct,
    sunshine_hours,
    rain_mm > 0                              as is_rain_hour

from joined