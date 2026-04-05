from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG

from assets import alerts_asset
from operators.bq_operator import _load_to_bigquery


with DAG(
    dag_id = "alerts_consumer",
    schedule=[alerts_asset],
    catchup=False,
    tags=["alerts", "consumer"],
):
    load_to_bigquery = PythonOperator(
        task_id = "load_to_bigquery",
        python_callable = _load_to_bigquery,
        op_kwargs={
            "gcs_path": "gs://alarms-intelligent-pipeline-raw-landing/{{ (triggering_asset_events.values() | first | first).extra.gcs_path }}",
        }
    )