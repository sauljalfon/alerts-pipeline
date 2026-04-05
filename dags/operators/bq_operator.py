import json
import logging
import pendulum
from google.cloud import storage, bigquery

logger = logging.getLogger(__name__)

PROJECT_ID = "alarms-intelligent-pipeline"
DATASET = "raw_dataset"
TABLE = "raw_alerts"

def _load_to_bigquery(**context):
    gcs_path = context["gcs_path"]
    suffix = pendulum.now("Asia/Jerusalem").format("YYYYMMDD_HHmmss")

    client = bigquery.Client()
    
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        schema=[
            bigquery.SchemaField("rid", "INTEGER"),
            bigquery.SchemaField("data", "STRING"),
            bigquery.SchemaField("date", "STRING"),
            bigquery.SchemaField("time", "STRING"),
            bigquery.SchemaField("alertDate", "STRING"),
            bigquery.SchemaField("category", "INTEGER"),
            bigquery.SchemaField("category_desc", "STRING"),
            bigquery.SchemaField("matrix_id", "INTEGER"),
        ],
    )

    temp_table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}_temp_{suffix}"

    load_job = client.load_table_from_uri(
        f"{gcs_path}",
        temp_table_id,
        job_config=job_config,
    )

    load_job.result()
    logger.info("Loaded data from %s to temporary table %s", gcs_path, temp_table_id)

    merge_query = f"""
        MERGE `{PROJECT_ID}.{DATASET}.{TABLE}` AS target
        USING `{temp_table_id}` AS source
        ON target.rid = source.rid
        WHEN NOT MATCHED THEN
            INSERT (rid, data, date, time, alertDate, category, category_desc, matrix_id, ingested_at)
            VALUES (source.rid, source.data, source.date, source.time, source.alertDate, source.category, source.category_desc, source.matrix_id, CURRENT_TIMESTAMP())
    """

    try:
        query_job = client.query(merge_query)
        query_job.result()
        logger.info("Merged data from temporary table %s to final table %s.%s.%s", temp_table_id, PROJECT_ID, DATASET, TABLE)

    except Exception as e:
        logger.error("Error merging data from temporary table %s to final table %s.%s.%s: %s", temp_table_id, PROJECT_ID, DATASET, TABLE, e)
        raise

    finally:
        client.delete_table(temp_table_id, not_found_ok=True)
        logger.info("Deleted temporary table %s", temp_table_id)