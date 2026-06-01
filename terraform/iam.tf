resource "google_service_account" "detector" {
  account_id   = "detector-sa"
  display_name = "Cost Sentinel Detector"
}

# BigQuery: read billing export tables and run query jobs
resource "google_project_iam_member" "detector_bq_viewer" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.detector.email}"
}

resource "google_project_iam_member" "detector_bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.detector.email}"
}

# Workload Identity: allows the Kubernetes SA "detector" in namespace "sentinel"
# to impersonate this GCP SA — no key file needed in the pod
resource "google_service_account_iam_member" "detector_workload_identity" {
  service_account_id = google_service_account.detector.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[sentinel/detector]"
}

output "detector_sa_email" {
  value = google_service_account.detector.email
}
