from src.clients.bigquery import BigQueryClient

_Z_THRESHOLD = 2.0


def scan(bq: BigQueryClient, project_id: str, dataset: str, table: str) -> list[dict]:
    # Build 7-day hourly baseline per service, compare against the most recent
    # complete hour. SAFE_DIVIDE handles services with zero stddev (flat spend).
    sql = f"""
    WITH hourly AS (
      SELECT
        service.description AS service,
        TIMESTAMP_TRUNC(usage_start_time, HOUR) AS hour,
        SUM(cost) AS hourly_cost
      FROM `{project_id}.{dataset}.{table}`
      WHERE usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 8 DAY)
      GROUP BY 1, 2
    ),
    baseline AS (
      SELECT
        service,
        AVG(hourly_cost) AS mean_cost,
        STDDEV(hourly_cost) AS stddev_cost
      FROM hourly
      WHERE hour < TIMESTAMP_TRUNC(TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR), HOUR)
      GROUP BY 1
    ),
    latest AS (
      SELECT
        service,
        SUM(hourly_cost) AS current_cost
      FROM hourly
      WHERE hour = TIMESTAMP_TRUNC(TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR), HOUR)
      GROUP BY 1
    )
    SELECT
      l.service,
      ROUND(l.current_cost, 4)  AS current_hour_usd,
      ROUND(b.mean_cost, 4)     AS baseline_mean_usd,
      ROUND(b.stddev_cost, 4)   AS baseline_stddev_usd,
      ROUND(SAFE_DIVIDE(l.current_cost - b.mean_cost, b.stddev_cost), 2) AS z_score
    FROM latest l
    JOIN baseline b USING (service)
    WHERE b.stddev_cost > 0
      AND SAFE_DIVIDE(l.current_cost - b.mean_cost, b.stddev_cost) > {_Z_THRESHOLD}
    ORDER BY z_score DESC
    """
    return bq.query(sql)
