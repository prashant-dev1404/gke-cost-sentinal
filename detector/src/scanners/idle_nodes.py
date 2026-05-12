from src.clients.prometheus import PrometheusClient

_CPU_USD_PER_VCPU_HOUR = 0.098  # GKE Autopilot asia-south1
_HOURS_PER_DAY = 24


def scan(prom: PrometheusClient, threshold: float) -> list[dict]:
    # node-exporter labels by `instance` (IP:port), not `node`.
    # avg by (instance) collapses the per-cpu/per-mode series to one per host.
    util_results = prom.query(
        '1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[1h]))'
    )

    # Count distinct CPU series per instance to get vCPU count without
    # joining across metric namespaces (node-exporter vs kube-state-metrics
    # share no common label in this cluster).
    vcpu_results = prom.query(
        'count by (instance) (node_cpu_seconds_total{mode="idle"})'
    )
    vcpus_by_instance = {
        r["metric"]["instance"]: float(r["value"][1])
        for r in vcpu_results
    }

    idle = []
    for r in util_results:
        instance = r["metric"].get("instance", "unknown")
        utilization = float(r["value"][1])
        if utilization < threshold:
            vcpus = vcpus_by_instance.get(instance, 1.0)
            daily_usd = vcpus * (1 - utilization) * _CPU_USD_PER_VCPU_HOUR * _HOURS_PER_DAY
            idle.append({
                "node": instance,
                "cpu_utilization_pct": round(utilization * 100, 2),
                "vcpus": int(vcpus),
                "estimated_daily_waste_usd": round(daily_usd, 2),
            })

    return idle
