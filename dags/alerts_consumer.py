from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.providers.standard.sensors.time_delta import TimeDeltaSensor
from airflow.sdk import DAG
from datetime import timedelta
from docker.types import Mount

from operators.bq_operator import _load_to_bigquery
from config import alerts_asset, DBT_IMAGE, DBT_SECRETS_SOURCE, DBT_PROFILES_SOURCE


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

    wait_for_bq = TimeDeltaSensor(
        task_id="wait_for_bq",
        delta=timedelta(seconds=30),
    )

    dbt_build = DockerOperator(
        task_id="dbt_build",
        image=DBT_IMAGE,
        command="build --project-dir /dbt --profiles-dir /root/.dbt",
        mounts=[
            Mount(
                source=DBT_SECRETS_SOURCE,
                target="/dbt/secrets",
                type="bind",
            ),
            Mount(
                source=DBT_PROFILES_SOURCE,
                target="/root/.dbt",
                type="bind",
            ),
        ],
        docker_url="unix://var/run/docker.sock",
        network_mode="bridge",
        auto_remove="success",
        mount_tmp_dir=False,
    )

    load_to_bigquery >> wait_for_bq >> dbt_build

