import httpx


class PrometheusClient:
    def __init__(self, base_url: str):
        self._base = base_url.rstrip("/")

    def query(self, promql: str) -> list[dict]:
        r = httpx.get(
            f"{self._base}/api/v1/query",
            params={"query": promql},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        if data["status"] != "success":
            raise RuntimeError(f"Prometheus error: {data.get('error')}")
        return data["data"]["result"]
