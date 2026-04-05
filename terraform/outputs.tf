output "raw_landing_bucket" {
  description = "GCS raw landing zone bucket name"
  value       = google_storage_bucket.raw_landing.name
}

output "bigquery_dataset" {
  description = "BigQuery dataset ID"
  value       = google_bigquery_dataset.raw_dataset.dataset_id
}

output "service_account_email" {
  description = "Pipeline service account email"
  value       = google_service_account.pipeline.email
}

resource "local_file" "service_account_key" {
  filename        = var.service_account_key_path
  content         = base64decode(google_service_account_key.pipeline.private_key)
  file_permission = "0600"
}

output "service_account_key_path" {
  description = "Path to the written service account key file"
  value       = local_file.service_account_key.filename
}
