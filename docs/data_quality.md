# Data quality notes

Findings from loading the raw data. Each one is handled later in dbt or reported as a limitation.

## Smart Dublin historical station data (May 2024 to June 2026)

Source: monthly `dublin-bikes_station_status_MMYYYY.csv` files from
[data.smartdublin.ie](https://data.smartdublin.ie/dataset/dublinbikes-api), loaded into `raw.dublinbikes_history`.

**Overall:** 26 files, 15,149,940 rows, 214,370 five-minute snapshots out of 227,808 possible (94.1%).

| Finding | Detail | How it is handled |
|---|---|---|
| Times are UTC | On 29 Mar 2026 (Irish clocks go forward at 01:00) every 01:00–01:55 snapshot is present, so the file is not in local time. | Treated as UTC, the same as the live feed. |
| Not every station is in every snapshot | About 71 of 114–115 stations appear per snapshot on average. A station seems to be written only when its status changes. | Carry each station's last known status forward in dbt before measuring time empty or full. |
| September 2024 is almost empty | Only 1 Sep 00:05 to 3 Sep 16:30 (774 of 8,640 snapshots). | Excluded from monthly comparisons. |
| 25 Jan to 5 Feb 2026 missing | January ends 24 Jan 23:55; February starts 5 Feb 16:55. | Reported as a gap. |
| Smaller gaps | May 2024 starts 2 May 19:00; Feb 2025 starts 1 Feb 16:50; one day missing in July 2025. | Coverage shown per month. |
| 00:00 on the 1st of each month is missing | Each file runs 00:05 to 23:55, so one slot falls between files. | Negligible. |
| March and April 2024 not published | No files on the portal. | History starts May 2024. |
| July 2026 to 4 Oct 2026 not published yet | The live collector starts 4 Oct 2026. | Reported as a gap between history and live data. |
| Station count changes | 114 stations until Nov 2024, 115 in most months from Dec 2024. | Station dimension built from all stations seen. |

## Live collector (from 4 Oct 2026)

| Finding | Detail | How it is handled |
|---|---|---|
| Missed runs on 5 Oct 2026 | Runs were cancelled or queued while GitHub Actions was degraded (githubstatus.com). | Short gap; no code change. |
| `last_reported` is often hours older than the feed time | Seen in the first snapshot; most stations report only when something changes. | Use the feed's `last_updated` as the snapshot time. |
| Stations 30 and 118 are not installed | `is_installed = false`. | Filtered out of reliability metrics. |
