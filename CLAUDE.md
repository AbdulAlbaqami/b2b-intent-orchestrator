# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

`hubspot-intent-pipeline` is part of the `Affiliate_Marketing_AI_Sys` project. It scrapes LinkedIn data, runs NLP-based intent matching, and feeds qualified leads into HubSpot CRM.

## Environment Setup

Python 3.14 with a local venv:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the Pipeline

```bash
source .venv/bin/activate
python main.py
```

## Architecture

The pipeline follows a linear ETL flow:

```
LinkedIn (scrape) → ingestion/ → intelligence/ → HubSpot (CRM push)
```

**`ingestion/`** — data collection layer
- `linkedin_scraper.py` — scrapes LinkedIn profiles/posts for lead data
- `utils.py` — shared helpers for ingestion (auth, pagination, rate limiting)

**`intelligence/`** — NLP processing layer
- `text_cleaning.py` — normalizes raw text before analysis
- `nlp_matcher.py` — classifies buyer intent signals in cleaned text

**`data/`** — local data store
- `raw/` — unprocessed scrape outputs
- `processed/` — NLP-enriched records ready for CRM push

**`orchestration/`** — pipeline scheduling and coordination (planned)

**`notebooks/`** — exploratory analysis and prototyping

**`tests/`** — test suite (planned)

**`issues/`** — tracked bugs and blockers

## Status

Most module files are stubs (`## hold`). `requirements.txt` is empty — add dependencies there as modules are implemented.
