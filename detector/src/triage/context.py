from datetime import datetime, timezone

from src.clients.kubernetes import get_client

_SYSTEM_NS_PREFIXES = ("kube-", "gke-", "gmp-", "monitoring", "istio-")
# ~3000 tokens at 4 chars/token; split proportionally across sections
_CHAR_BUDGET = 11_000
_SECTION_FRACTIONS = {"events": 0.40, "deployments": 0.30, "pdbs": 0.15, "pod_logs": 0.15}


def _is_user_ns(name: str) -> bool:
    return not any(name.startswith(p) for p in _SYSTEM_NS_PREFIXES) and name != "default"


def _fmt_event(e) -> str:
    ts = str(e.last_timestamp or e.first_timestamp or "")[:19]
    return f"{ts} [{e.type}] {e.involved_object.kind}/{e.involved_object.name}: {e.message}"


def _fmt_pdb(pdb) -> str:
    return (
        f"{pdb.metadata.namespace}/{pdb.metadata.name}: "
        f"minAvailable={pdb.spec.min_available} "
        f"allowedDisruptions={pdb.status.disruptions_allowed}"
    )


def _fmt_revision(rs) -> str:
    rev = (rs.metadata.annotations or {}).get("deployment.kubernetes.io/revision", "?")
    containers = rs.spec.template.spec.containers or []
    image = containers[0].image if containers else "unknown"
    ready = rs.status.ready_replicas or 0
    return f"  rev={rev} image={image} ready={ready}"


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit] + "\n[truncated]"


def gather_context(alert: dict) -> dict:
    core, apps, policy = get_client()
    alert_type = alert.get("type", "")
    resource = alert.get("resource", "")

    user_ns = [
        ns.metadata.name
        for ns in core.list_namespace().items
        if _is_user_ns(ns.metadata.name)
    ]

    # Events: collect from all user namespaces, sort by recency, keep last 50
    raw_events = []
    for ns in user_ns:
        try:
            raw_events.extend(core.list_namespaced_event(ns).items)
        except Exception:
            pass

    def _event_ts(e):
        ts = e.last_timestamp or e.first_timestamp
        return ts if ts else datetime.min.replace(tzinfo=timezone.utc)

    raw_events.sort(key=_event_ts)
    events_text = "\n".join(_fmt_event(e) for e in raw_events[-50:])

    # Deployment revisions: last 3 ReplicaSets per Deployment by revision annotation
    deploy_lines = []
    for ns in user_ns:
        try:
            for dep in apps.list_namespaced_deployment(ns).items:
                selector = ",".join(
                    f"{k}={v}" for k, v in (dep.spec.selector.match_labels or {}).items()
                )
                rs_list = apps.list_namespaced_replica_set(ns, label_selector=selector).items
                rs_list.sort(
                    key=lambda rs: int(
                        (rs.metadata.annotations or {}).get("deployment.kubernetes.io/revision", "0")
                    ),
                    reverse=True,
                )
                deploy_lines.append(f"Deployment {ns}/{dep.metadata.name}:")
                deploy_lines.extend(_fmt_revision(rs) for rs in rs_list[:3])
        except Exception:
            pass
    deploys_text = "\n".join(deploy_lines)

    # PDBs: all namespaces
    pdbs = policy.list_pod_disruption_budget_for_all_namespaces().items
    pdbs_text = "\n".join(_fmt_pdb(p) for p in pdbs)

    # Pod logs: only for idle_node alerts — map node IP to name, then sample one pod's logs
    logs_text = ""
    node_name = None
    if alert_type == "idle_node":
        node_ip = resource.split(":")[0]
        try:
            for node in core.list_node().items:
                for addr in (node.status.addresses or []):
                    if addr.type == "InternalIP" and addr.address == node_ip:
                        node_name = node.metadata.name
                        break
                if node_name:
                    break
        except Exception:
            pass

        if node_name:
            try:
                pods_on_node = core.list_pod_for_all_namespaces(
                    field_selector=f"spec.nodeName={node_name}"
                ).items
                for pod in pods_on_node:
                    if _is_user_ns(pod.metadata.namespace):
                        raw_logs = core.read_namespaced_pod_log(
                            pod.metadata.name,
                            pod.metadata.namespace,
                            tail_lines=50,
                            _request_timeout=10,
                        )
                        logs_text = (
                            f"Logs from {pod.metadata.namespace}/{pod.metadata.name}:\n{raw_logs}"
                        )
                        break
            except Exception:
                pass

    sections = {
        "events": events_text,
        "deployments": deploys_text,
        "pdbs": pdbs_text,
        "pod_logs": logs_text,
    }
    for key, fraction in _SECTION_FRACTIONS.items():
        sections[key] = _truncate(sections[key], int(_CHAR_BUDGET * fraction))

    return {
        **sections,
        "node_name": node_name,
        "counts": {
            "events": len(raw_events),
            "deploys": len(deploy_lines),
            "pdbs": len(pdbs),
        },
    }
