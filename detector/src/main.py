from fastapi import FastAPI
from src.config import settings
from src.clients.prometheus import PrometheusClient
from src.clients.bigquery import BigQueryClient
from src.scanners import idle_nodes, billing_anomaly
from src.triage import agent

app = FastAPI(title="GKE Cost Sentinel")

_prom = PrometheusClient(settings.prometheus_url)
_bq = BigQueryClient(settings.project_id)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/scan/idle-nodes")
def scan_idle_nodes():
    results = idle_nodes.scan(_prom, settings.idle_cpu_threshold)
    return {"count": len(results), "idle_nodes": results}


@app.get("/scan/billing-anomaly")
def scan_billing_anomaly():
    results = billing_anomaly.scan(
        _bq, settings.project_id, settings.bigquery_dataset, settings.billing_table
    )
    return {"count": len(results), "anomalies": results}


@app.post("/triage")
def triage_endpoint(alert: dict):
    return agent.triage(alert)
