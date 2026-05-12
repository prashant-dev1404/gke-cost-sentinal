from google.cloud import bigquery


class BigQueryClient:
    def __init__(self, project_id: str):
        self._client = bigquery.Client(project=project_id)

    def query(self, sql: str) -> list[dict]:
        rows = self._client.query(sql).result()
        return [dict(row) for row in rows]
