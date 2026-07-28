"""
checkout-service — serviço de exemplo do Curso 4 (CI/CD Inteligente).

O mesmo código roda como STABLE (v1) e como CANARY (v2). O comportamento é
controlado por variáveis de ambiente (os "botões de caos" do build) e por
feature flags lidas do flagd em tempo real (padrão OpenFeature, equivalente
open source ao LaunchDarkly).

Ideia central do curso: DEPLOY != RELEASE.
  - O deploy do canário (v2) coloca o código novo em produção recebendo tráfego.
  - O release do comportamento novo é controlado pela flag `new-checkout-flow`.
  - Se algo der errado, o `kill-switch` corta o recurso em milissegundos, sem
    precisar de rollback de imagem.

Variáveis de ambiente:
  APP_VERSION      -> "v1" (stable) ou "v2" (canary). Vira o label `version`.
  ERROR_RATE       -> probabilidade de falha [0.0 - 1.0] (simula build ruim).
  EXTRA_LATENCY_MS -> latência extra em ms (simula regressão de performance).
  FLAGD_OFREP_URL  -> base do endpoint OFREP do flagd (ex.: http://flagd:8016).
"""

import asyncio
import os
import random
import time
import uuid

import httpx
from fastapi import FastAPI, HTTPException, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# --------------------------------------------------------------------------- #
# Configuração via ambiente
# --------------------------------------------------------------------------- #
APP_VERSION = os.getenv("APP_VERSION", "v1")
ERROR_RATE = float(os.getenv("ERROR_RATE", "0.0"))
EXTRA_LATENCY_MS = int(os.getenv("EXTRA_LATENCY_MS", "0"))
FLAGD_OFREP_URL = os.getenv("FLAGD_OFREP_URL", "http://flagd:8016").rstrip("/")

app = FastAPI(title=f"checkout-service ({APP_VERSION})")

# --------------------------------------------------------------------------- #
# Métricas Prometheus
#   - http_requests_total{version,status}  -> success rate por versão
#   - http_request_duration_seconds{version} -> p50/p95/p99 por versão
# São exatamente os sinais que o Argo Rollouts (e o canary_controller.py deste
# lab) consultam para decidir PROMOVER ou fazer ROLLBACK do canário.
# --------------------------------------------------------------------------- #
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total de requisições HTTP no /checkout",
    ["version", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Latência das requisições HTTP no /checkout",
    ["version"],
)


# --------------------------------------------------------------------------- #
# Leitura de feature flags via OFREP (OpenFeature Remote Evaluation Protocol)
# --------------------------------------------------------------------------- #
async def eval_flag(key: str, default):
    """Avalia uma flag no flagd via OFREP. Nunca derruba a request:
    se o flagd estiver indisponível, cai no valor `default`."""
    url = f"{FLAGD_OFREP_URL}/ofrep/v1/evaluate/flags/{key}"
    # targetingKey aleatório por request -> distribui o rollout percentual
    payload = {"context": {"targetingKey": str(uuid.uuid4()), "version": APP_VERSION}}
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                return resp.json().get("value", default)
    except Exception:
        # flagd fora do ar -> comportamento seguro (default)
        return default
    return default


# --------------------------------------------------------------------------- #
# Middleware de métricas (instrumenta apenas o /checkout)
# --------------------------------------------------------------------------- #
@app.middleware("http")
async def monitor_requests(request, call_next):
    if request.url.path != "/checkout":
        return await call_next(request)

    start = time.time()
    status_code = 200
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except HTTPException as exc:  # noqa: F841 (re-levantada abaixo)
        status_code = exc.status_code
        raise
    except Exception:
        status_code = 500
        raise
    finally:
        REQUEST_LATENCY.labels(version=APP_VERSION).observe(time.time() - start)
        REQUEST_COUNT.labels(version=APP_VERSION, status=str(status_code)).inc()


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #
@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
def health():
    return {"status": "UP", "version": APP_VERSION}


@app.get("/flags")
async def flags():
    """Endpoint de depuração: mostra como este pod está enxergando as flags."""
    return {
        "version": APP_VERSION,
        "kill-switch": await eval_flag("kill-switch", False),
        "new-checkout-flow": await eval_flag("new-checkout-flow", False),
        "checkout-canary-rollout": await eval_flag("checkout-canary-rollout", False),
    }


@app.post("/checkout")
async def checkout():
    # 1) Kill-switch: corta o recurso instantaneamente (não depende de deploy).
    if await eval_flag("kill-switch", False):
        raise HTTPException(status_code=503, detail="Checkout desativado (kill-switch)")

    # 2) A flag `new-checkout-flow` decide se ESTE pod executa o fluxo novo.
    #    Deploy (v2 em produção) e release (flag ligada) são desacoplados.
    new_flow = await eval_flag("new-checkout-flow", False)

    # 3) Simula o processamento (pagamento/estoque).
    base_latency = random.uniform(0.05, 0.15)
    extra_latency = EXTRA_LATENCY_MS / 1000.0 if new_flow else 0.0
    await asyncio.sleep(base_latency + extra_latency)

    # 4) A taxa de erro do build só "vaza" quando o fluxo novo está liberado.
    effective_error = ERROR_RATE if new_flow else 0.0
    if random.random() < effective_error:
        raise HTTPException(status_code=500, detail="Falha no gateway de pagamento")

    return {
        "status": "SUCCESS",
        "version": APP_VERSION,
        "flow": "new" if new_flow else "legacy",
        "transaction_id": f"txn-{random.randint(1000, 9999)}",
    }
