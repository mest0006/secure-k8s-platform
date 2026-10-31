# hello-api runbook

## Error budget burn

**Alerts:** `HelloApiErrorBudgetFastBurn` (page), `HelloApiErrorBudgetSlowBurn` (ticket)

1. Check the "Error ratio" panel on the *hello-api SLOs* dashboard and confirm which status codes are rising.
2. `kubectl get pods -l app.kubernetes.io/name=hello-api` to check for restarts or pods that aren't Ready.
3. `kubectl logs deploy/hello-api --since=30m` and look for errors around the start of the burn.
4. If it started with a deploy, roll back: `helm rollback hello-api` (or redeploy the previous digest), then confirm the error ratio recovers.
5. Write a post-incident review: timeline, impact on the error budget, root cause, and the change that stops it happening again.

## Latency

**Alert:** `HelloApiLatencySLOBreach`

1. Check the p99 latency panel and request rate. A traffic spike points to capacity; flat traffic points to a code or dependency change.
2. `kubectl top pods -l app.kubernetes.io/name=hello-api` and check for CPU throttling against the 250m limit.
3. Scale out if needed (`kubectl scale deploy/hello-api --replicas=4`) and follow up with a requests and limits change in the chart.

## Pod won't start

- `ImagePullBackOff`: confirm the tag or digest exists in GHCR. Mutable tags are blocked by policy, so pin the digest from the CI summary.
- Admission denied by Kyverno: the message names the rule. Fix the manifest; don't add an exception without a review.
- `CrashLoopBackOff`: `kubectl logs --previous` to see why the last container exited.
