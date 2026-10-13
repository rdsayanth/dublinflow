# Power BI report

How the report in [`powerbi/`](../powerbi/) is built, and why. Screenshots are in the [README](../README.md#power-bi-report); the findings themselves are in [findings.md](findings.md).

## Format

The report is saved as a **Power BI Project (`.pbip`)**, not a `.pbix`:

- `DublinFlow.SemanticModel/definition/` holds the model in **TMDL**: one plain-text file per table, with every measure, column and relationship.
- `DublinFlow.Report/definition/` holds the report in **PBIR**: one JSON file per page and per visual.
- `.pbi/cache.abf` (the imported data) and `.pbi/localSettings.json` are gitignored.

Every change is a readable git diff, for example a one-line DAX fix shows up as one changed line.

## Data model

Import mode, PostgreSQL connector (`localhost`, database `dublinflow`, schema `analytics`). The tables come straight from the dbt marts; Power BI adds only a calendar table, one calculated column and the measures.

| Table | Rows | Role |
|---|---|---|
| `fct_station_hourly` | ~2.07M | Fact: one row per station per hour. Holds all measures (display folder *Measures*). |
| `dim_station` | 115 | Station name, location, capacity. |
| `dim_hour` | ~21.5K | Every hour since May 2024, Irish local time parts, weather, `is_service_hour`. Adds the calculated column `Day Type` (Weekday / Weekend). |
| `Date` | 1 per day | DAX calendar from 1 May 2024 to today, marked as the date table (for time intelligence). |
| `mart_station_reliability` | 115 | dbt's own score per station, used only for the cross-check. |

Relationships, all single direction except the last:

- `dim_station[station_id]` 1 → * `fct_station_hourly[station_id]`
- `dim_hour[hour_utc]` 1 → * `fct_station_hourly[hour_utc]`
- `Date[Date]` 1 → * `dim_hour[date_local]`
- `dim_station[station_id]` 1 ↔ 1 `mart_station_reliability[station_id]` (both directions, Power BI's default for one-to-one; harmless because the mart links to nothing else)

Auto date/time is off, so Power BI doesn't create hidden date tables.

## Measures (22)

| Group | Measures |
|---|---|
| Base | Station Hours, In-Service Hours, % Empty, % Full, % Out of Service |
| Score | Reliability Score = `100 × (1 − % Empty − % Full)`, blank when a selection has no in-service time |
| Weather | Score (Dry), Score (Rain), Rain Effect |
| Time | Score Same Period Last Year, Change vs Last Year, Score Rolling 3 Months |
| Stations | Station Rank, Best Station, Worst Station |
| dbt cross-check | dbt Score Check, Stations Checked, Stations Matching dbt, dbt Check Result, dbt Check Colour, dbt Mismatch, dbt Mismatch List |

All base measures filter to service hours (`dim_hour[is_service_hour] = TRUE()`), exactly like the dbt mart.

## Design decisions

**Rank against the whole station table.** `Station Rank` first used `RANKX(ALLSELECTED(dim_station[station_name]), ...)`. In the Stations table each row is also filtered by `capacity` (the Docks column), and that filter stayed, so every station was ranked only against stations with the same number of docks (Fenian Street 1st, Sandwith Street also 1st). `ALLSELECTED(dim_station)` removes the filters from every station column and still respects slicers. `HASONEVALUE` keeps the Total row blank.

**Cross-check DAX against dbt.** The score is calculated twice: in SQL by dbt (`mart_station_reliability`) and in DAX from the 2M-row fact table. The Data and method page shows "115 of 115 stations match dbt", and lists any station that differs. Differences under 0.05 count as a match, so floating-point noise can't raise a false alarm. If someone later changes one side and not the other, the card turns red.

**Best and Worst Station skip blanks.** `TOPN` sorts blank scores first in ascending order, so a station with no data in the selected dates would have been the "worst". The measures filter out blank scores first.

**Dot map instead of Azure Maps.** Azure Maps needs a work or school Power BI sign-in, so anyone opening the project from GitHub would see a sign-in message. The station map is a scatter chart of longitude and latitude, coloured red to green by score. The axis ranges are set so 1 km looks about the same east-west and north-south.

**Import, not DirectQuery.** The data changes at most a few times a day, and Import gives fast visuals and full DAX (time intelligence, RANKX). The cost is a manual refresh: see below.

**Slicers change their own page only.** On the Stations page, the station slicer changes only the hourly chart; the table and the Best/Worst cards always show all stations.

**Custom theme.** `StaticResources/RegisteredResources/DublinFlowTheme.json`: navy header band, cobalt blue and orange as the two series colours (easy to tell apart, including for most colour-blind viewers), white rounded tiles. Red to yellow to green is used only where it means bad to good (heatmap, map).

## Refreshing

1. `scripts/refresh_warehouse.ps1` loads new data and runs `dbt build` every morning (Windows Task Scheduler). See the [README](../README.md#refreshing-the-data).
2. Open `powerbi/DublinFlow.pbip` and click **Refresh**. Power BI Desktop cannot refresh on a schedule; that needs the Power BI service.
3. Check the Data and method page still says every station matches dbt.
