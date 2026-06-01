import os
from kubernetes import client, config as k8s_config


def get_client() -> tuple[client.CoreV1Api, client.AppsV1Api, client.PolicyV1Api]:
    if os.getenv("KUBERNETES_SERVICE_HOST"):
        k8s_config.load_incluster_config()
    else:
        k8s_config.load_kube_config()
    return client.CoreV1Api(), client.AppsV1Api(), client.PolicyV1Api()
