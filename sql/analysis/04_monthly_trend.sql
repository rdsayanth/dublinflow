-- 04 Is reliability getting better or worse over time?
-- City-wide Reliability Score per month (service hours), with window functions:
--   LAG(x)      compares each month with the month before
--   LAG(x, 12)  compares each month with the same month last year
--   AVG() OVER  gives a rolling 3-month average that smooths out noisy months
-- Trap: LAG() looks at the previous ROW, not the previous month. There is no data for
-- Jul to Sep 2026 (history ends June 2026, live collection starts 4 Oct 2026), so without
-- a full list of months LAG would compare Oct 2026 with June 2026. The "months" CTE builds
-- every month with generate_series, so missing months appear as empty rows and LAG stays honest.
-- days_with_data flags thin months (Sep 2024 has only 3 days).
with monthly as (

    select
        date_trunc('month', h.date_local)::date            as month,
        count(distinct h.date_local)                       as days_with_data,
        count(*)                                           as station_hours,
        100 * (1 - avg(f.share_empty) - avg(f.share_full)) as reliability_score,
        100 * avg(f.share_empty)                           as pct_empty,
        100 * avg(f.share_full)                            as pct_full
    from analytics.fct_station_hourly as f
    join analytics.dim_hour as h
        on h.hour_utc = f.hour_utc
    where h.is_service_hour
      and f.share_empty is not null
    group by date_trunc('month', h.date_local)

),

months as (

    select generate_series(min(month), max(month), interval '1 month')::date as month
    from monthly

)

select
    months.month,
    coalesce(monthly.days_with_data, 0)                          as days_with_data,
    round(monthly.pct_empty, 1)                                  as pct_empty,
    round(monthly.pct_full, 1)                                   as pct_full,
    round(monthly.reliability_score, 1)                          as reliability_score,
    round(monthly.reliability_score
          - lag(monthly.reliability_score) over (order by months.month), 1)     as change_vs_last_month,
    round(monthly.reliability_score
          - lag(monthly.reliability_score, 12) over (order by months.month), 1) as change_vs_last_year,
    round(avg(monthly.reliability_score) over (
        order by months.month
        rows between 2 preceding and current row
    ), 1)                                                        as rolling_3_month_score
from months
left join monthly
    on monthly.month = months.month
order by months.month;