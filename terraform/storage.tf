resource "google_storage_bucket" "raw_landing" {
  name                        = "${var.project_id}-raw-landing"
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}
