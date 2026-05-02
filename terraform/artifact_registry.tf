resource "google_artifact_registry_repository" "sentinel" {
  location      = var.region
  repository_id = "sentinel"
  description   = "Container images for the cost-sentinel project"
  format        = "DOCKER"
}
