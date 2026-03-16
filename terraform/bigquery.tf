resource "google_bigquery_dataset" "info_dataset" {
  dataset_id  = "info_dataset"
  location    = var.region
  description = "Raw ingestion dataset for alarms and weather data"
}

resource "google_bigquery_table" "raw_alerts" {
  dataset_id          = google_bigquery_dataset.info_dataset.dataset_id
  table_id            = "raw_alerts"
  deletion_protection = false

  schema = jsonencode([
    { name = "ingested_at", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "alert_id",    type = "STRING",    mode = "NULLABLE" },
    { name = "alert_date",  type = "TIMESTAMP", mode = "NULLABLE" },
    { name = "area",        type = "STRING",    mode = "NULLABLE" },
    { name = "area_en",     type = "STRING",    mode = "NULLABLE" },
    { name = "category",    type = "STRING",    mode = "NULLABLE" },
    { name = "threat",      type = "STRING",    mode = "NULLABLE" },
    { name = "raw_payload", type = "JSON",      mode = "NULLABLE" },
  ])
}

resource "google_bigquery_table" "raw_weather" {
  dataset_id          = google_bigquery_dataset.info_dataset.dataset_id
  table_id            = "raw_weather"
  deletion_protection = false

  schema = jsonencode([
    { name = "ingested_at",   type = "TIMESTAMP", mode = "REQUIRED" },
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
