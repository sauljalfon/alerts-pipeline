# Israel Alarms Intelligence Pipeline

## Goal
Ingest Tzeva Adom alerts + weather data, enrich,
store in BigQuery, visualize in Grafana,
generate daily sitrep with LLM.

## Stack
Airflow, Terraform, GCS, BigQuery, dbt, Grafana, Claude API

## GCP Project
alarms-intelligent-pipeline

## Structure
/dags       → Airflow DAGs
/terraform  → GCP IaC
/dbt        → transformation models
/grafana    → dashboard configs
/tests      → DAG + dbt tests