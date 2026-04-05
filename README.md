# Israel Alarms Pipeline

An end-to-end data pipeline that ingests live Tzeva Adom (Israeli rocket alert) data, enriches it, stores it in BigQuery, and surfaces it through an AI-powered Streamlit dashboard.

## Architecture

```
oref.org.il API
      │
      ▼
[Airflow: alerts_producer]
      │  fetches alerts + saves to GCS
      ▼
Google Cloud Storage (raw landing)
      │
      ▼
[Airflow: alerts_consumer]
      │  loads + deduplicates into BigQuery
      ▼
BigQuery: raw_dataset.raw_alerts
      │
      ▼
[dbt]
  staging_dataset.stg_alarms__alarms   ← cleaned view
  analysis_dataset.fct_alerts          ← enriched with city data (lat/lon, population)
      │
      ▼
Streamlit Dashboard
  ├── Data tab      → filterable table + charts
  ├── Map tab       → geographic heatmap of alerts
  └── Chat tab      → natural language Q&A via Gemini 2.5 Pro (text-to-SQL)
```

## Stack

| Layer | Technology |
|---|---|
| Orchestration | Apache Airflow 3 |
| Infrastructure | Terraform + GCP |
| Storage | Google Cloud Storage |
| Warehouse | BigQuery |
| Transformation | dbt (BigQuery adapter) |
| Dashboard | Streamlit |
| AI | Google Gemini 2.5 Pro |

## Project Structure

```
.
├── dags/
│   ├── alerts_producer.py        # Fetches alerts from oref API → GCS
│   ├── alerts_consumer.py        # GCS → BigQuery (triggered by asset)
│   ├── assets.py                 # Airflow asset definitions
│   └── operators/
│       ├── oref_operator.py      # oref.org.il scraper
│       ├── gcs_operators.py      # GCS upload logic
│       └── bq_operator.py        # BigQuery merge logic
├── dbt/
│   ├── models/
│   │   ├── staging/alarms/       # stg_alarms__alarms (view)
│   │   ├── staging/cities/       # stg_cities__cities (view)
│   │   └── marts/                # fct_alerts (table, enriched)
│   ├── seeds/
│   │   └── cities.csv            # City reference data (name, lat, lon, population)
│   └── macros/
│       └── generate_schema_name.sql
├── streamlit/
│   ├── app.py                    # Dashboard application
│   ├── Dockerfile
│   └── requirements.txt
├── terraform/
│   ├── main.tf                   # GCP provider + APIs
│   ├── bigquery.tf               # Datasets + tables
│   ├── storage.tf                # GCS bucket (raw landing, 90-day lifecycle)
│   ├── iam.tf                    # Service account + permissions
│   └── variables.tf
├── docker-compose.yaml           # Airflow (official image)
├── docker-compose.override.yml   # Project-specific overrides + Streamlit service
└── secrets/
    └── service-account-key.json  # GCP credentials (not committed)
```

## BigQuery Datasets

| Dataset | Description |
|---|---|
| `raw_dataset` | Raw ingestion — `raw_alerts`, `raw_weather` tables |
| `staging_dataset` | dbt staging views — cleaned and typed |
| `analysis_dataset` | dbt marts — `fct_alerts` enriched with city metadata |

## Prerequisites

- Docker + Docker Compose
- GCP project with billing enabled
- Terraform >= 1.5
- A GCP service account key with BigQuery + GCS permissions
- A [Google AI Studio](https://aistudio.google.com) API key (free) for the chatbot

## Setup

### 1. GCP Infrastructure

```bash
cd terraform
terraform init
terraform apply -var="project_id=alarms-intelligent-pipeline" -var="region=US"
```

### 2. Environment Variables

Create a `.env` file at the project root:

```env
GCP_PROJECT_ID=alarms-intelligent-pipeline
GEMINI_API_KEY=your_gemini_api_key_here
AIRFLOW_UID=50000
```

### 3. Secrets

Place your GCP service account key at:

```
secrets/service-account-key.json
```

### 4. Start the Stack

```bash
docker compose up -d
```

Services:
- Airflow UI → http://localhost:8080 (admin / admin)
- Streamlit dashboard → http://localhost:8501

### 5. Seed City Reference Data

```bash
cd dbt
dbt seed
```

### 6. Run the Pipeline

Trigger `alerts_producer` manually from the Airflow UI. It will:
1. Fetch the latest alerts from oref.org.il
2. Save them to GCS
3. Automatically trigger `alerts_consumer` (via asset)
4. Load and deduplicate into `raw_dataset.raw_alerts`

### 7. Run dbt Transformations

```bash
cd dbt
dbt run
```

This builds `stg_alarms__alarms`, `stg_cities__cities`, and `fct_alerts`.

## Dashboard

The Streamlit app at `http://localhost:8501` has three tabs:

### Data
Filterable table of all alerts with search by city, category, and date range. Includes metrics (total alerts, cities affected, tracking window) and charts (alerts by category, by hour of day, and over time).

### Map
Geographic heatmap of Israel showing alert frequency by city. Dots are sized proportionally to alert count. Includes a top 10 most targeted cities leaderboard.

### Ask Me About the Data
AI chatbot powered by Gemini 2.5 Pro. Uses a text-to-SQL approach:
1. Your question → Gemini generates a BigQuery SQL query
2. Query runs on BigQuery
3. Results → Gemini answers in plain English

Each response shows the SQL query and raw results for transparency.

## Development

To update `app.py` without rebuilding:

```bash
docker compose restart streamlit
```

To rebuild after changing `requirements.txt`:

```bash
docker compose build streamlit && docker compose up -d streamlit
```

To run dbt tests:

```bash
cd dbt && dbt test
```
