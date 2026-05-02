resource "google_bigquery_dataset" "billing" {
  dataset_id  = "billing_export"
  location    = "asia-south1"
  description = "GCP billing export destination, queried by the cost-sentinel detector"

  delete_contents_on_destroy = true
}
