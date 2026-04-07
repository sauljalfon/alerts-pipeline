import os
from airflow.sdk import Asset

# ── Assets ────────────────────────────────────────────────────────────────────
alerts_asset = Asset("gs://alarms-intelligent-pipeline-raw-landing/alerts/")

# ── dbt ───────────────────────────────────────────────────────────────────────
DBT_IMAGE = os.environ.get("DBT_IMAGE", "dbt-alarms")
DBT_SECRETS_SOURCE = os.environ.get("DBT_SECRETS_SOURCE", "/home/saul-server/alerts-pipeline/secrets")
DBT_PROFILES_SOURCE = os.environ.get("DBT_PROFILES_SOURCE", "/home/saul-server/.dbt")
