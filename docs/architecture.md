# DublinFlow architecture

## Overview

```mermaid
flowchart LR
    subgraph Cloud
        GBFS[Dublin Bikes GBFS feed] --> GHA[GitHub Actions<br/>every 10 min<br/>Python collector]
        GHA --> BLOB[(Azure Blob Storage<br/>raw JSON)]
    end
    subgraph Local
        BLOB --> LOADER[Python loader]
        HIST[Smart Dublin<br/>historical CSVs] --> LOADER
        MET[Met Éireann<br/>hourly weather] --> LOADER
        LOADER --> RAW[(PostgreSQL<br/>raw schema)]
        RAW --> DBT[dbt Core<br/>staging, intermediate, marts<br/>+ tests]
        DBT --> SQL[SQL analysis<br/>Reliability Score]
        SQL --> PBI[Power BI report]
    end
```

## Why this design

| Decision | Reason |
|---|---|
| Collector runs in GitHub Actions, not on my laptop | Data keeps collecting every 10 minutes even when the laptop is off. Free for public repos. |
| Raw JSON stored in Azure Blob Storage | Cheap, durable storage for raw files. Keeping the raw data means any later step can be re-run from scratch. |
| PostgreSQL runs locally | Free, and the data volume is small enough for one machine. |
| dbt for transformations | SQL models are version-controlled, tested and documented, with clear layers. |
| Power BI only at the end | The report reads from tested marts, so the numbers can be trusted. |

## Key data rules

- Snapshots show **availability, not trips**. Any "activity" measured from changes between snapshots is a proxy, because rebalancing vans also move bikes.
- Dublin Bikes timestamps are **UTC**. Met Éireann recent data is **Irish local time**. They are aligned carefully, including daylight saving changes.
- Weather comes from **one station** (Dublin Airport), so it is city-wide, not per bike station.
- The feed's own timestamps are used, not the time the collector ran, because GitHub Actions schedules can be delayed.

## Reliability Score

`100 × (1 − share of time empty − share of time full)`, during service hours.
Empty % and full % are also reported separately. No arbitrary weights.
