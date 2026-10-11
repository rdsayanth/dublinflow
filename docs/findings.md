# Findings

What the data says about the project question: **how reliable is it to find a bike, or a free dock, at a Dublin Bikes station, and how do time, weather and location change that?**

Data: Smart Dublin station history (May 2024 to June 2026) plus the live feed collected by this project (from 4 October 2026), aggregated to one row per station per hour in `fct_station_hourly`. Weather: Met Éireann, Dublin Airport, hourly. Analysis run on 11 October 2026. Queries are in [`sql/analysis/`](../sql/analysis/).

## How reliability is measured

**Reliability Score = 100 × (1 − share of time empty − share of time full)**, measured during service hours only.

- **Empty** = 0 bikes (you can't rent). **Full** = 0 free docks (you can't return).
- **Service hours** = 05:00 to 23:59 Irish time. Bikes can be rented 05:00 to 00:30 (Dublin City Council). The feed does not mark the night closure, so the rule is applied from the clock.
- **Out of service** = 0 bikes *and* 0 docks at the same time (docks switched off). This time is left out of the score and reported separately, otherwise it would count as both empty and full.
- Each service hour counts equally. The score is built in dbt (`mart_station_reliability`) and tested to stay between 0 and 100.

## 1. Station ranking ([01](../sql/analysis/01_station_ranking.sql))

| | Station | Score | Empty % | Full % |
|---|---|---|---|---|
| Best | Fenian Street | 98.1 | 1.1 | 0.8 |
| | Sandwith Street | 97.7 | 1.4 | 0.9 |
| | Emmet Road | 96.1 | 2.6 | 1.3 |
| Worst | Hardwicke Place | 57.2 | 42.8 | 0.0 |
| | Eccles Street East | 58.9 | 41.0 | 0.1 |
| | Heuston Station (Central) | 63.7 | 17.0 | 19.3 |
| | Grangegorman Lower (Central) | 66.4 | 33.6 | 0.0 |

- **Empty is the bigger problem than full.** Most of the 15 lowest-scoring stations are in the north inner city (around Dorset Street, Mountjoy Square, Grangegorman) and are empty for 25% to 43% of service hours.
- **Heuston is different:** its stations are often full as well as empty, which fits train commuters arriving and leaving (inferred).
- Caveat: York Street West (station 51) was out of service 66% of the time, so its score rests on only 4,454 hours; Barrow Street has about 7,800 hours, roughly half the others.

## 2. Time of day ([02](../sql/analysis/02_time_of_day.sql))

- **Weekdays follow the commute.** Empty stations rise from 7.8% at 07:00 to **13.8% at 10:00**, fall to 7.9% at 15:00, and climb again from 17:00 to 12.7% at 23:00.
- **Weekends have one midday peak** (12.6% empty at 12:00), and more stations are full in the daytime than on weekdays (about 4.8% vs 1.5%).
- **Best weekday times to find a bike: 07:00 and 15:00** (about 9% of station-hours empty or full).

## 3. Weather ([03](../sql/analysis/03_rain_vs_dry.sql))

| Weekdays | Station-hours | Empty % | Full % | Score |
|---|---|---|---|---|
| Dry | 1,008,073 | 11.1 | 2.9 | 85.9 |
| Light rain (under 1 mm) | 108,157 | 9.6 | 2.4 | 88.0 |
| Heavy rain (1 mm or more) | 32,757 | 8.6 | 2.4 | 89.0 |

- **Rain makes stations more reliable**, by about 3 points on weekdays (weekends: 86.1 dry, 88.3 heavy rain). Likely reason: fewer people ride, so fewer stations get emptied or filled (inferred).
- Caveats: heavy rain is rare (about 285 hours), weather is one station for the whole city, and season and time of day are not controlled for.

## 4. Trend over time ([04](../sql/analysis/04_monthly_trend.sql))

- **Reliability improved:** empty stations fell from 12–14% in mid and late 2024 to 9–10% in 2025–26; the rolling 3-month score rose from about 84 to about 87.
- Every month from May 2025 to April 2026 beat the same month a year earlier (by 0.4 to 3.3 points). May and June 2026 were slightly worse than 2025 (−0.8, −1.0), so the improvement may be levelling off.
- **Seasonal pattern:** winter is best (88–89 in December to February). **October is the worst month in both years** (81.9 in 2024, 84.5 in 2025).
- No data for July to September 2026 (history ends June 2026; live collection starts October 2026). The query uses a full list of months so these gaps show instead of being skipped.

## 5. Longest empty streaks ([05](../sql/analysis/05_empty_streaks.sql))

Hours in a row with a station empty for the whole hour:

| Station | Started (Irish time) | Hours | Days |
|---|---|---|---|
| Grangegorman Lower (Central) | Fri 7 Nov 2025, 09:00 | 99 | 4.1 |
| Rathdown Road | Mon 10 Feb 2025, 10:00 | 79 | 3.3 |
| Merrion Square South | Fri 24 Jan 2025, 11:00 | 69 | 2.9 |
| Fitzwilliam Square East | Sat 11 May 2024, 10:00 | 45 | 1.9 |
| Merrion Square East | Fri 27 Jun 2025, 17:00 | 42 | 1.8 |
| Merrion Square West | Fri 27 Jun 2025, 17:00 | 41 | 1.7 |

- Some stations stay empty for **days**, which means no bikes were brought back (rebalanced) in that time.
- Merrion Square East and West went empty at the same hour, which points to an event or an operational reason rather than normal demand (inferred). The Merrion Square South streak starts on 24 January 2025, the day of Storm Éowyn (possible link, not checked).

## Limitations

- Snapshots show availability, not trips. Empty and full times are a sign of imbalance, but rebalancing vans also move bikes.
- History has gaps (most of September 2024, 25 January to 5 February 2026); see [data_quality.md](data_quality.md).
- Weather comes from one station (Dublin Airport) for the whole city, and live-period weather arrives monthly.
- Results are averages over all hours; a station's score can hide very different weekday and weekend behaviour.
