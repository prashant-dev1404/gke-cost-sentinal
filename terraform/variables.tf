variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for regional resources"
  type        = string
  default     = "asia-south1"
}

variable "cluster_name" {
  description = "Name for the GKE Autopilot cluster"
  type        = string
  default     = "sentinel-cluster"
}
