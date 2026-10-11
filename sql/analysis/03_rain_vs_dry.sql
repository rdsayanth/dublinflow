-- 03 Does rain change how often stations are empty or full?
-- Weather is one station (Dublin Airport) for the whole city. Rain in the bike hour HH:00
-- comes from the Met Éireann row stamped HH+1:00 (joined in dim_hour).
-- Hours without weather yet (live period, Met Éireann publishes monthly) are left out.
with hourly as (

    select
        case
            when h.rain_mm = 0 then '1 dry'
            when h.rain_mm < 1 then '2 light (under 1 mm)'
            else                    '3 heavy (1 mm or more)'
        end                                              as rain_band,
        case when h.is_weekend then 'weekend' else 'weekday' end as day_type,
        f.share_empty,
        f.share_full
    from analytics.fct_station_hourly as f
    join analytics.dim_hour as h
        on h.hour_utc = f.hour_utc
    where h.is_service_hour
      and h.rain_mm is not null
      and f.share_empty is not null

)

select
    day_type,
    rain_band,
    count(*)                                                    as station_hours,
    round(100 * avg(share_empty), 1)                            as pct_empty,
    round(100 * avg(share_full), 1)                             as pct_full,
    round(100 * (1 - avg(share_empty) - avg(share_full)), 1)    as reliability_score
from hourly
group by day_type, rain_band
order by day_type, rain_band;