resource "google_bigquery_dataset" "raw_dataset" {
  dataset_id    = "raw_dataset"
  location      = var.region
  description   = "Raw ingestion dataset for alarms and weather data"
  delete_contents_on_destroy = true

  depends_on = [google_project_service.apis]
}

resource "google_bigquery_dataset" "staging_dataset" {
  dataset_id    = "staging_dataset"
  location      = var.region
  description   = "dbt staging layer - views over raw data"
  delete_contents_on_destroy = true

  depends_on = [google_project_service.apis]
}

resource "google_bigquery_dataset" "analysis_dataset" {
  dataset_id    = "analysis_dataset"
  location      = var.region
  description   = "dbt marts layer - enriched tables for analysis and dashboards"
  delete_contents_on_destroy = true

  depends_on = [google_project_service.apis]
}

resource "google_bigquery_table" "raw_alerts" {
  dataset_id          = google_bigquery_dataset.raw_dataset.dataset_id
  table_id            = "raw_alerts"
  deletion_protection = false

  schema = jsonencode([
    { name = "rid",             type = "INTEGER",   mode = "NULLABLE" },
    { name = "data",            type = "STRING",    mode = "NULLABLE" },
    { name = "date",            type = "STRING",    mode = "NULLABLE" },
    { name = "time",            type = "STRING",    mode = "NULLABLE" },
    { name = "alertDate",       type = "STRING",    mode = "NULLABLE" },
    { name = "category",        type = "INTEGER",   mode = "NULLABLE" },
    { name = "category_desc",   type = "STRING",    mode = "NULLABLE" },
    { name = "matrix_id",       type = "INTEGER",   mode = "NULLABLE" },
    { name = "ingested_at",     type = "TIMESTAMP", mode = "NULLABLE" },
  ])
}

resource "google_bigquery_table" "raw_weather" {
  dataset_id          = google_bigquery_dataset.raw_dataset.dataset_id
  table_id            = "raw_weather"
  deletion_protection = false

  schema = jsonencode([
    { name = "ingested_at",   type = "TIMESTAMP", mode = "NULLABLE" },
    { name = "observed_at",   type = "TIMESTAMP", mode = "NULLABLE" },
    { name = "location",      type = "STRING",    mode = "NULLABLE" },
    { name = "latitude",      type = "FLOAT64",   mode = "NULLABLE" },
    { name = "longitude",     type = "FLOAT64",   mode = "NULLABLE" },
    { name = "temp_celsius",  type = "FLOAT64",   mode = "NULLABLE" },
    { name = "humidity_pct",  type = "FLOAT64",   mode = "NULLABLE" },
    { name = "wind_speed_ms", type = "FLOAT64",   mode = "NULLABLE" },
    { name = "wind_dir_deg",  type = "FLOAT64",   mode = "NULLABLE" },
    { name = "condition",     type = "STRING",    mode = "NULLABLE" },
    { name = "raw_payload",   type = "JSON",      mode = "NULLABLE" },
  ])
}
