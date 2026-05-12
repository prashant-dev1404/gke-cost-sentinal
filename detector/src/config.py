from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    prometheus_url: str = "http://localhost:9090"
    project_id: str = "cost-sentinel-13402"
    bigquery_dataset: str = "billing_export"
    # Wildcard matches the table GCP auto-creates; name encodes billing account ID
    billing_table: str = "gcp_billing_export_v1_*"
    idle_cpu_threshold: float = 0.10

    model_config = {"env_prefix": "SENTINEL_"}


settings = Settings()
