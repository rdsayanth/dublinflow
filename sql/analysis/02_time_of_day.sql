-- 02 When are stations empty or full?
-- City-wide average by Irish local hour, weekdays vs weekends, service hours only.
-- FILTER (WHERE ...) splits one average into columns without a second query.
with hourly as (

    select
        h.hour_of_day_local,
        h.is_weekend,
        f.share_empty,
        f.share_full
    from analytics.fct_station_hourly as f
    join analytics.dim_hour as h
        on h.hour_utc = f.hour_utc
    where h.is_service_hour
      and f.share_empty is not null          -- skip hours fully out of service

)

select
    hour_of_day_local,
    round(100 * avg(share_empty) filter (where not is_weekend), 1) as weekday_pct_empty,
    round(100 * avg(share_empty) filter (where is_weekend), 1)     as weekend_pct_empty,
    round(100 * avg(share_full)  filter (where not is_weekend), 1) as weekday_pct_full,
    round(100 * avg(share_full)  filter (where is_weekend), 1)     as weekend_pct_full
from hourly
group by hour_of_day_local
order by hour_of_day_local;