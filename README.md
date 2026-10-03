DublinFlow: Dublin Bikes Reliability Data Platform

Work in progress. Currently in Phase 1 of 9 (project setup).

The question

How reliable is it to find a bike, or a free dock, at a Dublin Bikes station? And how do weather, time of day and location change that?

What this project does

An end-to-end data pipeline:

A Python collector reads the live Dublin Bikes feed every 10 minutes (scheduled with GitHub Actions) and saves the raw JSON to Azure Blob Storage.
A Python loader brings the raw files, historical station data and Met Éireann weather into PostgreSQL.
dbt models clean, join and test the data (staging, intermediate, marts).
SQL analysis calculates a Reliability Score for each station.
A Power BI report presents the findings.

See docs/architecture.md for the design.

Reliability Score

100 × (1 − share of time empty − share of time full), measured during service hours. Empty % and full % are also reported separately.

Tech stack

Python 3.12 · requests · PostgreSQL · dbt Core · GitHub Actions · Azure Blob Storage · Power BI

Repository structure
ingestion/          Python collectors and loaders
dbt/                dbt project (models and tests)
sql/                DDL and analysis queries
tests/              Python tests
powerbi/            Power BI report and screenshots
docs/               Architecture, data dictionary, findings
.github/workflows/  GitHub Actions schedules
Getting started (Windows)
git clone https://github.com/rdsayanth/dublinflow.git
cd dublinflow
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Data sources and attribution
Dublin Bikes live station feed (GBFS): station status and station information.
Smart Dublin: historical Dublin Bikes station data.
Met Éireann: hourly weather observations for Dublin Airport. Copyright Met Éireann. Source: www.met.ie. Licensed under CC BY 4.0.
Author

Sayanth Rajani Divakaran · GitHub