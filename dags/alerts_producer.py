from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG
from airflow.timetables.interval import CronDataIntervalTimetable

from config import alerts_asset
from operators.gcs_operators import _save_to_gcs
from operators.oref_operator import _fetch_alerts

with DAG(
    dag_id = "alerts_producer",
    schedule=CronDataIntervalTimetable("0 */6 * * *", timezone="Asia/Jerusalem"),
    catchup=False,
    tags=["alerts", "producer"],
):
    fetch_alerts = PythonOperator(
        task_id = "fetch_alerts",
        python_callable = _fetch_alerts,
    )

    save_to_gcs = PythonOperator(
        task_id = "save_to_gcs",
        python_callable = _save_to_gcs,
        outlets = [alerts_asset],
    )

    fetch_alerts >> save_to_gcs