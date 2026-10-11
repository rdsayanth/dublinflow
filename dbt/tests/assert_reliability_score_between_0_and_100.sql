-- A score outside 0 to 100 means the empty and full shares are wrong.
-- dbt test passes when this query returns no rows.
select station_id, reliability_score
from {{ ref('mart_station_reliability') }}
where reliability_score < 0
   or reliability_score > 100