#!/usr/bin/env bash
#
# DEMO 1 — canário RUIM: gate reprova e o Argo Rollouts faz rollback sozinho.
#
# Sobe o build v2 com 35% de erro e +400ms de latência. A AnalysisTemplate mede,
# reprova e o Rollout aborta, devolvendo 100% do tráfego para o stable.
# Tempo esperado: ~45s até `Degraded`.
#
#   ./demo-canary-ruim.sh
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

echo "→ disparando canário RUIM (v2, ERROR_RATE=0.35, EXTRA_LATENCY_MS=400)…"
# A annotation `demo-run` muda o pod-template a cada execução, garantindo uma
# revisão nova mesmo que o spec já estivesse nestes valores.
kubectl patch rollout checkout --type=json -p="[
  {\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/env/0/value\",\"value\":\"v2\"},
  {\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/env/1/value\",\"value\":\"0.35\"},
  {\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/env/2/value\",\"value\":\"400\"},
  {\"op\":\"add\",\"path\":\"/spec/template/metadata/annotations/demo-run\",\"value\":\"$(date +%s)\"}
]" >/dev/null

echo "→ esperado: setWeight 10% → Paused → Analysis Failed → Degraded (rollback)"
echo
kubectl argo rollouts get rollout checkout --watch
