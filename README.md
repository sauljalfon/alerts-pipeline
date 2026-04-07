# Israel Alarms Intelligence Pipeline

An end-to-end data pipeline that ingests live Tzeva Adom (Israeli rocket alert) data, enriches it with city metadata, stores it in BigQuery, and surfaces it through an AI-powered Streamlit dashboard.

## Architecture

```
oref.org.il API
      │
      ▼
[Airflow: alerts_producer]  ← runs every 6 hours (Asia/Jerusalem)
      │  fetches alerts → saves to GCS
      ▼
Google Cloud Storage (raw landing)
      │
      ▼
[Airflow: alerts_consumer]  ← triggered automatically via GCS asset
      │  deduplicates + loads into BigQuery
      ▼
BigQuery: raw_dataset.raw_alerts
      │
      ▼
[dbt]  ← runs inside isolated Docker container via DockerOperator
  staging_dataset.stg_alarms__alarms   ← cleaned view
  analysis_dataset.fct_alerts          ← enriched with city data (lat/lon, population)
      │
      ▼
Streamlit Dashboard
  ├── Data tab   → filterable table + charts
  ├── Map tab    → geographic heatmap of alerts
  └── Chat tab   → natural language Q&A via Gemini 2.5 Pro (text-to-SQL)
```

## Stack

| Layer | Technology |
|---|---|
| Orchestration | Apache Airflow 3 |
| Infrastructure | Terraform + GCP |
| Storage | Google Cloud Storage |
| Warehouse | BigQuery |
| Transformation | dbt (BigQuery adapter, runs in Docker) |
| Dashboard | Streamlit (deployed on Streamlit Cloud + self-hosted) |
| AI | Google Gemini 2.5 Pro |
| Containerization | Docker + Docker Compose |

## Project Structure

```
.
├── dags/
│   ├── alerts_producer.py        # Fetches alerts from oref API → GCS (every 6h)
│   ├── alerts_consumer.py        # GCS → BigQuery → dbt build (asset-triggered)
│   ├── config.py                 # Shared constants and Airflow asset definitions
│   └── operators/
│       ├── oref_operator.py      # oref.org.il scraper
│       ├── gcs_operators.py      # GCS upload logic
│       └── bq_operator.py        # BigQuery merge/dedup logic
├── dbt/
│   ├── Dockerfile                # Standalone dbt image (dbt-bigquery:1.9.0)
│   ├── models/
│   │   ├── staging/alarms/       # stg_alarms__alarms (view)
│   │   ├── staging/cities/       # stg_cities__cities (view)
│   │   └── marts/                # fct_alerts (table, enriched)
│   ├── seeds/
│   │   └── cities.csv            # City reference data (name, lat, lon, population)
│   └── macros/
│       └── generate_schema_name.sql
├── streamlit/
│   ├── app.py                    # Dashboard (supports Streamlit Cloud secrets + Docker)
│   ├── Dockerfile
│   └── requirements.txt
├── terraform/
│   ├── main.tf                   # GCP provider + APIs
│   ├── bigquery.tf               # Datasets + tables
│   ├── storage.tf                # GCS bucket (raw landing, 90-day lifecycle)
│   ├── iam.tf                    # Service account + permissions
│   └── variables.tf
├── docker-compose.yaml           # Official Airflow stack
├── docker-compose.override.yml   # Project overrides + Streamlit service
└── secrets/
    └── service-account-key.json  # GCP credentials (not committed)
```

## BigQuery Datasets

| Dataset | Description |
|---|---|
| `raw_dataset` | Raw ingestion — `raw_alerts` table + cities seed |
| `staging_dataset` | dbt staging views — cleaned and typed |
| `analysis_dataset` | dbt marts — `fct_alerts` enriched with city metadata |

## Prerequisites

- Docker + Docker Compose
- GCP project with billing enabled
- Terraform >= 1.5
- GCP service account key with BigQuery + GCS permissions
- [Google AI Studio](https://aistudio.google.com) API key for the chatbot

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
AIRFLOW_UID=50000
GCP_PROJECT_ID=alarms-intelligent-pipeline
GEMINI_API_KEY=your_gemini_api_key
_PIP_ADDITIONAL_REQUIREMENTS=apache-airflow-providers-docker

# dbt paths (adjust per environment)
DBT_SECRETS_SOURCE=/path/to/secrets
DBT_PROFILES_SOURCE=/path/to/.dbt
DBT_KEYFILE_PATH=/path/to/secrets/service-account-key.json
```

### 3. Secrets

Place your GCP service account key at:

```
secrets/service-account-key.json
```

### 4. dbt Profile

Create `~/.dbt/profiles.yml`:

```yaml
alarms_pipeline:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: service-account
      project: alarms-intelligent-pipeline
      dataset: info_dataset
      location: me-west1
      keyfile: "{{ env_var('DBT_KEYFILE_PATH', '/dbt/secrets/service-account-key.json') }}"
      threads: 4
```

### 5. Build the dbt Docker Image

```bash
docker build -t dbt-alarms ./dbt
```

### 6. Start the Stack

```bash
docker compose up airflow-init  # first time only
docker compose up -d
```

Services:
- Airflow UI → http://localhost:8080 (airflow / airflow)
- Streamlit dashboard → http://localhost:8501

### 7. Run the Pipeline

Trigger `alerts_producer` manually from the Airflow UI, or wait for the 6-hour schedule. It will:

1. Fetch the latest alerts from oref.org.il
2. Save them to GCS
3. Automatically trigger `alerts_consumer` via Airflow asset
4. Deduplicate and load into `raw_dataset.raw_alerts`
5. Wait 30 seconds, then run `dbt build` in a Docker container
6. Build `fct_alerts` in `analysis_dataset` — ready for the dashboard

## Streamlit Cloud Deployment

The app supports both Docker (via `GOOGLE_APPLICATION_CREDENTIALS`) and Streamlit Cloud (via `st.secrets`).

Add the following to Streamlit Cloud **Settings → Secrets**:

```toml
GCP_PROJECT_ID = "alarms-intelligent-pipeline"
GEMINI_API_KEY = "your-gemini-api-key"

[gcp_service_account]
type = "service_account"
project_id = "alarms-intelligent-pipeline"
private_key_id = "..."
private_key = "..."
client_email = "..."
# ... rest of the service account JSON fields
```

## Dashboard

### Data
Filterable table of all alerts with search by city, category, and date range. Includes metrics (total alerts, cities affected, tracking window) and charts (alerts by category, hour of day, and over time).

### Map
Geographic heatmap of Israel showing alert frequency by city. Dot size scales with alert count. Includes a top 10 most targeted cities leaderboard.

### Ask Me About the Data
AI chatbot powered by Gemini 2.5 Pro using a text-to-SQL approach:
1. Your question → Gemini generates a BigQuery SQL query
2. Query runs on BigQuery
3. Results → Gemini answers in plain English

Each response shows the generated SQL and raw results for transparency.

## Development

Rebuild the dbt image after model changes:
```bash
docker build -t dbt-alarms ./dbt
```

Rebuild Streamlit after dependency changes:
```bash
docker compose build streamlit && docker compose up -d streamlit
```

Run dbt manually:
```bash
cd dbt && uv run dbt build --profiles-dir ~/.dbt
```

Run dbt tests:
```bash
cd dbt && uv run dbt test --profiles-dir ~/.dbt
```
