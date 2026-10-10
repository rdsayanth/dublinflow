# Data quality notes

Findings from loading and modelling the raw data. Each one is handled in dbt or reported as a limitation.

## Smart Dublin historical station data (May 2024 to June 2026)

Source: monthly `dublin-bikes_station_status_MMYYYY.csv` files from
[data.smartdublin.ie](https://data.smartdublin.ie/dataset/dublinbikes-api), loaded into `raw.dublinbikes_history`.

**Overall:** 26 files, 15,149,940 rows, 214,370 five-minute snapshots out of 227,808 possible (94.1%).

| Finding | Detail | How it is handled |
|---|---|---|
| Times are UTC | On 29 Mar 2026 (Irish clocks go forward at 01:00) every 01:00–01:55 snapshot is present, so the file is not in local time. | Treated as UTC, the same as the live feed. |
| Not every station is in every snapshot | About 71 of 114–115 stations appear per snapshot. Tested (1–7 Jun 2026): 72% of rows are identical to the station's previous row, so stations are **not** written only on change. Gaps between a station's rows: 5 min 34.6%, 10–15 min 65.3%, over 1 hour 0.1%. Stations report about every 10 minutes while snapshots are every 5. | Main table is one row per station per hour (`fct_station_hourly`), averaging the 6–12 readings in each hour. No forward-fill; station-hours with no reading are left out. |
| One row per station per snapshot | dbt uniqueness test on all 15.1M rows passes. | Tested in `stg_dublinbikes_history`. |
| September 2024 is almost empty | Only 1 Sep 00:05 to 3 Sep 16:30 (774 of 8,640 snapshots). | Excluded from monthly comparisons. |
| 25 Jan to 5 Feb 2026 missing | January ends 24 Jan 23:55; February starts 5 Feb 16:55. | Reported as a gap. |
| Smaller gaps | May 2024 starts 2 May 19:00; Feb 2025 starts 1 Feb 16:50; one day missing in July 2025. | Coverage shown per month. |
| 00:00 on the 1st of each month is missing | Each file runs 00:05 to 23:55, so one slot falls between files. | Negligible. |
| March and April 2024 not published | No files on the portal. | History starts May 2024. |
| July 2026 to 4 Oct 2026 not published yet | The live collector starts 4 Oct 2026. | Reported as a gap between history and live data. |
| Station count changes | 114 stations until Nov 2024, 115 in most months from Dec 2024. | `dim_station` built from all stations seen (115). |

## Live collector (from 4 Oct 2026)

| Finding | Detail | How it is handled |
|---|---|---|
| Missed runs on 5 Oct 2026 | Runs were cancelled or failed while GitHub Actions was degraded (githubstatus.com). | Short gap; no code change. |
| `last_reported` is unreliable | Checked 4–10 Oct 2026: for 96% of rows a station's `last_reported` is over an hour older than the feed time. Yet in 29% of consecutive snapshots where `last_reported` did not change, the bike count did change (similar to the 28% change rate in the history). | Counts are treated as live. The feed's `last_updated` is used as the snapshot time; `last_reported` is kept but not used. |
| Stations 30 and 118 are not installed | `is_installed = false`. | Filtered out of `fct_station_hourly`. |
| Data can go stale if the loader is not run | Live files reach PostgreSQL only when `load_raw_to_postgres.py` runs. | dbt source freshness on `raw.gbfs_snapshot`: warn after 2 days, error after 7. |

## Met Éireann hourly weather, Dublin Airport (station 532)

| Finding | Detail | How it is handled |
|---|---|---|
| Times are UTC | Stated in the file legend. | Parsed with `date::timestamp` (not `to_timestamp()`, which applies the session time zone). |
| Rain is stamped at the end of the hour | Hourly rain at HH:00 is taken as the total for the hour ending HH:00 (usual convention for these files; not stated in the legend). | The bike hour starting HH:00 is joined to the weather row stamped HH+1:00 in `dim_hour`. |
| Quality code 111 ("investigation required") | Seen on many recent hours in the rain, temperature and wind indicators; the values are still present. | Values kept; `rain_quality_code` carried in `stg_weather_hourly`. |
| Blank values in older years only | A few blanks (visibility, cloud) before 2024; none from May 2024 to Aug 2026. | Blanks become NULL in staging. |
| Published monthly | The file ends 1 Sep 2026, so the live period has no weather yet. | `dim_hour` has NULL weather for those hours until the loader is re-run. |