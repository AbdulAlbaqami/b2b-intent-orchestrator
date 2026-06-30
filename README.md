# Intent Pipeline
B2B Intent Data Pipeline & Agentic Orchestrator.

## Quickstart
    source venv/bin/activate        # Windows: .\venv\Scripts\activate
    pip install -e ".[dev]"
    cp .env.example .env
    pytest

## Architecture
Decoupled layers: Ingestion (L1), Intelligence (L2), Identity Resolution (L2.5),
Storage (L3), Orchestrator (L4). See CLAUDE.md for the full map and agent rules.
