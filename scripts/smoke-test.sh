#!/usr/bin/env bash
# Port-forward to the service and check every endpoint the platform relies on.
set -euo pipefail

kubectl rollout status deployment/hello-api --timeout=90s
kubectl port-forward svc/hello-api 18080:80 >/tmp/port-forward.log 2>&1 &
PF=$!
trap 'kill $PF 2>/dev/null || true' EXIT

for i in $(seq 1 20); do
  curl -fsS http://127.0.0.1:18080/healthz >/dev/null 2>&1 && break
  sleep 1
done

curl -fsS http://127.0.0.1:18080/ | grep -q '"message"'
curl -fsS http://127.0.0.1:18080/readyz | grep -q '"ready": true'
curl -fsS http://127.0.0.1:18080/metrics | grep -q 'http_requests_total'
echo "smoke test passed"
