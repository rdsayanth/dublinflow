-- 01 Station ranking by Reliability Score (service hours 05:00-23:59 local).
-- Score = 100 x (1 - share of time empty - share of time full); out-of-service time excluded.
-- Result (11 Oct 2026, May 2024 to Oct 2026): best Fenian Street 98.1, worst Hardwicke Place 57.2.
select
    reliability_rank,
    station_id,
    station_name,
    capacity,
    in_service_hours,
    pct_out_of_service,
    pct_empty,
    pct_full,
    reliability_score
from analytics.mart_station_reliability
order by reliability_rank;