variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "alarms-intelligent-pipeline"
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "me-west1"
}

variable "service_account_key_path" {
  description = "Local path where the service account key JSON will be written"
  type        = string
  default     = "../service-account-key.json"
}
