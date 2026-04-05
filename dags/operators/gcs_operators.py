import json
import logging
import pendulum
from google.cloud import storage
from airflow.sdk import Metadata

from assets import alerts_asset

logger = logging.getLogger(__name__)

BUCKET_NAME = "alarms-intelligent-pipeline-raw-landing"

def _save_to_gcs(**context):
    data = context["ti"].xcom_pull(task_ids="fetch_alerts")
    now = pendulum.now("Asia/Jerusalem")
    gcs_relative_path = f"alerts/{now.format('YYYY/MM/DD/HHmm')}.json"

    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(gcs_relative_path)
    blob.upload_from_string(
        "\n".join(json.dumps(alert) for alert in data),
        content_type="application/json"
    )

    logger.info("Saved %d alerts to GCS: %s", len(data), gcs_relative_path)
    yield Metadata(alerts_asset, extra={"gcs_path": gcs_relative_path})
    
