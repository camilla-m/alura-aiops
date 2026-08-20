#!/usr/bin/env bash
#
# DEMO 2 — canário BOM: todos os gates passam e o Argo Rollouts promove sozinho.
#
# Sobe o build v2 saudável (sem erro, sem latência extra). A AnalysisTemplate
# aprova nos três gates e o Rollout avança 10% → 25% → 50% → 100%.
# Tempo esperado: ~2,5min até `Healthy`.
#
#   ./demo-canary-bom.sh
#
set -euo pipefail
cd "$(dirname "$0")"

# O gate precisa de tráfego para ter o que medir.
if ! kubectl get pod loadgen >/dev/null 2>&1; then
  echo "→ subindo o gerador de tráfego (loadgen)…"
  kubectl run loadgen --image=curlimages/curl --restart=Never -- \
    /bin/sh -c 'while true; do curl -s -X POST http://checkout-canary/checkout >/dev/null; sleep 0.1; done'
  kubectl wait --for=condition=Ready pod/loadgen --timeout=90s
fi

echo "→ disparando canário BOM (v2, ERROR_RATE=0.0, EXTRA_LATENCY_MS=0)…"
# A annotation `demo-run` muda o pod-template a cada execução, garantindo uma
# revisão nova mesmo que o spec já estivesse nestes valores.
kubectl patch rollout checkout --type=json -p="[
  {\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/env/0/value\",\"value\":\"v2\"},
  {\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/env/1/value\",\"value\":\"0.0\"},
  {\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/env/2/value\",\"value\":\"0\"},
  {\"op\":\"add\",\"path\":\"/spec/template/metadata/annotations/demo-run\",\"value\":\"$(date +%s)\"}
]" >/dev/null

echo "→ esperado: 10% → 25% → 50% → 100%, com Analysis Successful em cada gate"
echo
kubectl argo rollouts get rollout checkout --watch
