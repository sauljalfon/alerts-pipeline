resource "google_service_account" "pipeline" {
  account_id   = "alarms-pipeline-sa"
  display_name = "Alarms Intelligent Pipeline Service Account"
}

locals {
  pipeline_roles = [
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/bigquery.dataViewer",
    "roles/bigquery.readSessionUser",
    "roles/storage.objectAdmin",
  ]
}

resource "google_project_iam_member" "pipeline" {
  for_each = toset(local.pipeline_roles)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_service_account_key" "pipeline" {
  service_account_id = google_service_account.pipeline.name
}
