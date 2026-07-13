"""
Vídeo 4.5 — Hands-on: Investigação operacional com IA e logs
==============================================================
EXERCÍCIO PRÁTICO — Aula 4

Neste hands-on você vai investigar um incidente combinando:
  1. Post-mortem assistido por IA (4.1)
  2. Detecção de padrões recorrentes (4.2)
  3. Clustering de logs (4.3)
  4. Análise de sequências (4.4)

Cenário:
  O checkout-service está retornando erros intermitentes desde as 14h.
  Você recebe 500+ linhas de logs e precisa isolar a causa raiz em
  menos de 10 minutos usando as técnicas aprendidas.

Execute:
  python ai_log_investigation_lab.py
"""

from __future__ import annotations

import re
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class LogLine:
    timestamp: datetime
    level: str
    service: str
    message: str


@dataclass
class ClusterResult:
    pattern: str
    count: int
    level: str
    samples: list[str]
    is_anomaly: bool


def tokenize(msg: str) -> str:
    p = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '<IP>', msg)
    p = re.sub(r'[0-9a-f-]{36}', '<UUID>', p)
    p = re.sub(r'=\d+(\.\d+)?', '=<N>', p)
    p = re.sub(r'\b\d{3,}\b', '<N>', p)
    return p


def generate_incident_logs() -> list[LogLine]:
    """Gera logs do incidente com a causa raiz escondida."""
    base = datetime(2024, 8, 22, 14, 0, 0)
    logs: list[LogLine] = []

    # Normal traffic logs (alto volume)
    for i in range(150):
        ts = base + timedelta(seconds=i * 0.4)
        logs.append(LogLine(ts, "INFO", "api-gateway",
            f"GET /api/products from 10.0.1.{i % 50 + 10} — 200 in {40 + i % 30}ms"))

    for i in range(80):
        ts = base + timedelta(seconds=i * 0.7)
        logs.append(LogLine(ts, "INFO", "auth-service",
            f"Token validated for user usr-{2000 + i} (scope=read,write)"))

    # Checkout normal (para contraste)
    for i in range(30):
        ts = base + timedelta(seconds=i * 2)
        logs.append(LogLine(ts, "INFO", "checkout-service",
            f"Checkout completed for cart-{3000 + i} — total=R${50 + i * 10}.00"))

    # *** CAUSA RAIZ: Redis connection pool leak após deploy ***
    # Deploy event
    logs.append(LogLine(base + timedelta(minutes=5), "INFO", "deploy-controller",
        "Deploy checkout-service v5.2.0 completed (commit: abc123def)"))

    # Sintomas sutis que crescem
    for i in range(20):
        ts = base + timedelta(minutes=6, seconds=i * 15)
        pool = 80 + i * 1  # Pool crescendo
        logs.append(LogLine(ts, "WARN", "checkout-service",
            f"Redis connection pool utilization={pool}% (max=100, active={pool})"))

    # Erros começam
    for i in range(15):
        ts = base + timedelta(minutes=10, seconds=i * 8)
        logs.append(LogLine(ts, "ERROR", "checkout-service",
            f"Failed to acquire Redis connection — pool exhausted "
            f"(active=100/100, waiting=12) cart_id=cart-{4000 + i}"))

    # Cascata para payment
    for i in range(10):
        ts = base + timedelta(minutes=12, seconds=i * 10)
        logs.append(LogLine(ts, "ERROR", "payment-service",
            f"Checkout session expired — upstream timeout from checkout-service "
            f"txn_id=txn-{5000 + i}"))

    # Retry storms
    for i in range(25):
        ts = base + timedelta(minutes=13, seconds=i * 3)
        logs.append(LogLine(ts, "WARN", "checkout-service",
            f"Retry attempt {(i % 3) + 1}/3 for Redis operation — backoff={2 ** (i % 3)}s"))

    # Health check noise
    for i in range(40):
        ts = base + timedelta(seconds=i * 15)
        logs.append(LogLine(ts, "INFO", "k8s-probe",
            f"Health check /healthz — 200 OK (checkout-service pod-{i % 3})"))

    # Sequência anômala: checkout sem inventory check
    for i in range(5):
        ts = base + timedelta(minutes=14, seconds=i * 20)
        logs.append(LogLine(ts, "ERROR", "checkout-service",
            f"Checkout bypassed inventory check — Redis unavailable, "
            f"proceeding with stale data cart_id=cart-{6000 + i}"))

    return sorted(logs, key=lambda l: l.timestamp)


def cluster_logs(logs: list[LogLine]) -> list[ClusterResult]:
    pattern_map: dict[str, list[LogLine]] = {}
    for log in logs:
        pat = tokenize(log.message)
        pattern_map.setdefault(pat, []).append(log)

    total = len(logs)
    clusters = []
    for pat, entries in pattern_map.items():
        levels = Counter(e.level for e in entries)
        dom_level = levels.most_common(1)[0][0]
        is_anom = len(entries) < total * 0.03 and dom_level in ("ERROR", "WARN", "FATAL")
        clusters.append(ClusterResult(
            pattern=pat, count=len(entries), level=dom_level,
            samples=[e.message for e in entries[:2]], is_anomaly=is_anom,
        ))
    return sorted(clusters, key=lambda c: c.count, reverse=True)


def build_ai_prompt(anomaly_clusters: list[ClusterResult], deploy_info: str) -> str:
    """Constrói prompt para IA analisar as anomalias encontradas."""
    anomalies_text = ""
    for c in anomaly_clusters:
        anomalies_text += f"\n[{c.level}] {c.count}x ocorrências:\n"
        for s in c.samples:
            anomalies_text += f"  - {s}\n"

    return f"""Você é um SRE sênior. Analise as anomalias de logs abaixo e identifique a causa raiz.

CONTEXTO:
- Deploy recente: {deploy_info}
- Incidente começou ~5 minutos após o deploy

ANOMALIAS DETECTADAS (por clustering automático):
{anomalies_text}

TAREFA:
1. Qual é a causa raiz mais provável?
2. Qual é a cadeia de causalidade (A causou B que causou C)?
3. Quais ações imediatas tomar?
4. Como prevenir recorrência?

Seja objetivo e cite evidências dos logs."""


def run_lab() -> None:
    print("=" * 70)
    print("🔬 HANDS-ON: Investigação Operacional com IA e Logs")
    print("   Curso 3 — Observabilidade Inteligente — Aula 4")
    print("=" * 70)
    print("\n  📋 Cenário: checkout-service com erros intermitentes desde 14h")
    print("  🎯 Objetivo: Isolar a causa raiz em < 10 minutos")
    time.sleep(0.3)

    logs = generate_incident_logs()
    print(f"\n  📥 {len(logs)} linhas de log recebidas")

    # PASSO 1: Visão geral
    print(f"\n{'─' * 70}")
    print("PASSO 1/4 — Visão geral dos logs")
    print(f"{'─' * 70}")
    levels = Counter(l.level for l in logs)
    services = Counter(l.service for l in logs)
    print(f"\n  Por nível: {dict(levels)}")
    print(f"  Por serviço: {dict(services.most_common(5))}")
    print(f"  Período: {logs[0].timestamp.strftime('%H:%M')} — {logs[-1].timestamp.strftime('%H:%M')}")
    time.sleep(0.3)

    # PASSO 2: Clustering
    print(f"\n{'─' * 70}")
    print("PASSO 2/4 — Clustering automático de logs")
    print(f"{'─' * 70}")
    clusters = cluster_logs(logs)
    print(f"\n  {len(logs)} linhas → {len(clusters)} padrões\n")

    for i, c in enumerate(clusters[:8]):
        tag = " 🚨" if c.is_anomaly else ""
        pct = c.count / len(logs) * 100
        print(f"  #{i+1} [{c.level:5}] {c.count:>4}x ({pct:>5.1f}%) {c.samples[0][:55]}...{tag}")
    time.sleep(0.3)

    # PASSO 3: Foco nas anomalias
    print(f"\n{'─' * 70}")
    print("PASSO 3/4 — Análise de anomalias")
    print(f"{'─' * 70}")
    anomalies = [c for c in clusters if c.is_anomaly]
    print(f"\n  🚨 {len(anomalies)} padrões anômalos detectados:\n")
    for c in anomalies:
        print(f"  ❌ [{c.level}] {c.count}x: {c.samples[0][:65]}...")

    # Deploy correlation
    deploy_logs = [l for l in logs if "deploy" in l.service.lower() or "deploy" in l.message.lower()]
    deploy_info = deploy_logs[0].message if deploy_logs else "N/A"
    print(f"\n  🏷️  Deploy correlacionado: {deploy_info}")

    # Prompt para IA
    prompt = build_ai_prompt(anomalies, deploy_info)
    print(f"\n  🤖 Prompt gerado para IA ({len(prompt)} chars)")
    time.sleep(0.3)

    # PASSO 4: Diagnóstico
    print(f"\n{'─' * 70}")
    print("PASSO 4/4 — Diagnóstico (simulação da resposta da IA)")
    print(f"{'─' * 70}")
    print(f"""
  🎯 CAUSA RAIZ IDENTIFICADA:

  O deploy do checkout-service v5.2.0 introduziu um bug de connection
  leak no cliente Redis. Após o deploy, as conexões Redis não são
  devolvidas ao pool corretamente, causando esgotamento progressivo.

  📊 CADEIA DE CAUSALIDADE:
  ─────────────────────────────────────────────
  1. Deploy v5.2.0 (14:05) → novo código com connection leak
  2. Pool Redis cresce de 80% → 100% em ~5 min
  3. checkout-service não consegue conexão Redis → timeout
  4. Checkout bypassa inventory check (dados stale) → risco!
  5. payment-service timeout por cascata → transações falham
  6. Retry storms agravam a situação

  ✅ AÇÕES IMEDIATAS:
  ─────────────────────────────────────────────
  1. [AGORA]  Rollback checkout-service para v5.1.x
  2. [AGORA]  Forçar release de conexões Redis stale
  3. [CURTO]  Investigar commit abc123def (connection leak)
  4. [MÉDIO]  Adicionar alerta de pool utilization > 85%
  5. [LONGO]  Implementar circuit breaker para Redis
    """)

    # Relatório final
    print("=" * 70)
    print("📋 MÉTRICAS DO EXERCÍCIO")
    print("=" * 70)
    print(f"""
  Logs analisados        : {len(logs)}
  Padrões extraídos      : {len(clusters)}
  Anomalias isoladas     : {len(anomalies)}
  Redução de volume      : {(1 - len(clusters) / len(logs)) * 100:.0f}%
  Tempo de diagnóstico   : ~5 min (vs. 45+ min manual)
  Técnicas utilizadas    : Clustering + Sequência + IA Prompt
    """)

    print("=" * 70)
    print("🎓 FIM DO HANDS-ON — AULA 4 CONCLUÍDA!")
    print("=" * 70)
    print("""
  Você aprendeu a:
  ✔ Gerar post-mortems estruturados com assistência de IA
  ✔ Identificar padrões recorrentes em histórico de incidentes
  ✔ Agrupar logs automaticamente para isolar anomalias
  ✔ Detectar quebras de sequência em workflows operacionais
  ✔ Combinar clustering + IA para diagnóstico rápido

  Próxima aula: Operações orientadas por observabilidade inteligente →
    """)


if __name__ == "__main__":
    run_lab()
