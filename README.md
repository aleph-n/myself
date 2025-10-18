
# Myself: Personal Data Warehouse & AI-Powered Self-Analysis

## Project Overview
Myself is a Python-based system for capturing, structuring, and analyzing personal life data. It transforms daily logs into a rich data warehouse, enabling deep self-reflection and AI-powered feedback.


## Data Pipeline
The project operates a three-stage pipeline:

### 1. Capture (Raw Artifact)
- **How:** Log thoughts, events, and feelings in markdown files (`data/journal/`).
- **Tool:** `make log TEXT="..."` or manual edits. Entries are timestamped and appended via `src/journal.py`.
- **Output:** Unstructured markdown lines (Spanglish, free-form).

### 2. Enrich (AI Transformation)
- **How:** Extract, parse, and enrich raw entries using the Gemini API.
- **Tool:** Planned: `make ingest` runs `src/ingest.py`.
- **Process:**
    - Extracts new entries from markdown files.
    - Parses timestamps and text.
    - Sends prompts to Gemini for translation, categorization, sentiment, emotion, and behavioral analysis.
- **Output:** Structured JSON objects per entry (see below).

Example enriched entry:
```json
{
    "timestamp": "2025-10-15T14:30:00-06:00",
    "prompt_clean": "I read a chapter of 'Superintelligence'.",
    "category": "Knowledge & Research",
    "sentiment": "Neutral",
    "emotion": "Neutral/Informative",
    "behaviour": "Declarative"
}
```

### 3. Load (Structured Storage)
- **How:** Store enriched data in PostgreSQL for analysis and visualization.
- **Tool:** Planned: `src/ingest.py` connects to the DB and loads JSON objects into tables (e.g., `fact_prompts`).
- **Output:** Rows in the DWH, ready for queries and dashboards.

## Technology Stack
- **Backend:** Python 3.11+, FastAPI
- **Database:** PostgreSQL 16
- **Orchestration:** Docker & Docker Compose
- **Automation:** Makefile
- **AI/NLP:** Google Gemini API
- **Data Libraries:** Pandas, Psycopg2

## Project Structure
```
myself/
├── .env                  # API keys (add to .gitignore)
├── .gitignore
├── data/
│   ├── ddl/              # Database schema (01-schema.sql)
│   └── journal/          # Raw daily logs
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── output/
│   ├── reflections/      # AI-generated feedback
│   └── myself_prompts_enriched.csv
├── requirements.txt
├── README.md
└── src/
    ├── journal.py        # Log utility
    ├── process_journal.py  # Enrichment script
    ├── ingest.py         # Planned: CSV/JSON loader
    └── main.py           # FastAPI server
```
