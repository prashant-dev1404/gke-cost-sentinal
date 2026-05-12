# broken-batch — intentional cost waste scenario

## What it is

A 3-replica Deployment that requests 500m CPU + 512Mi memory per pod but does
nothing — each container runs `sleep 60` in an infinite loop. It also has a
PodDisruptionBudget with `minAvailable: 3`, which equals the replica count.

## The waste

GKE Autopilot bills for *requested* resources, not actual usage. These three
pods collectively request 1.5 vCPU + 1.5 GB of memory:

- CPU: 3 × 500m × $0.098/vCPU-hr ≈ $0.147/hr = **~$3.53/day**
- Memory: 3 × 512Mi × $0.0098/GB-hr ≈ $0.015/hr = **~$0.35/day**
- **Total: ~$3.88/day** for zero useful work

This shows up in billing export within ~24 hours and is the signal the
`/scan/billing-anomaly` and `/scan/idle-nodes` endpoints are designed to catch.

## Why the PDB blocks drain

Node drain is a voluntary disruption. The Kubernetes eviction API respects
PodDisruptionBudgets: before evicting a pod it checks that doing so won't
violate the budget. With `minAvailable: 3` and only 3 replicas, evicting even
one pod would leave 2 running — a violation. The autoscaler sees this, backs
off, and the node stays live indefinitely.

## The right fix

Change the PDB to `minAvailable: 2` (or equivalently `maxUnavailable: 1`).
That allows one pod to be disrupted at a time, unblocking node drain. The
deeper fix is to right-size resource requests to match actual usage, or delete
the Deployment entirely if the batch job has finished.

## Why a Deployment and not a Job

Kubernetes Jobs terminate when their pods complete. A sleeping pod never
exits, so a Job would keep restarting it — which is actually the correct
behaviour for a completed batch job that forgot to clean up. Using a
Deployment here makes the stuck-node scenario more visible in Prometheus
(the pods stay Running, not CrashLoopBackOff).
