# Israel Alarms Intelligence Pipeline

## Goal
Ingest Tzeva Adom alerts + weather data, enrich,
store in BigQuery, visualize in Streamlit,
generate daily sitrep with LLM.

## Stack
Airflow, Terraform, GCS, BigQuery, dbt, Streamlit, Claude API

## GCP Project
alarms-intelligent-pipeline

## Structure
/dags       → Airflow DAGs
/terraform  → GCP IaC
/dbt        → transformation models
/streamlit  → Streamlit dashboard app
/tests      → DAG + dbt tests