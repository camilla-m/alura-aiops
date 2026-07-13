"""
Vídeo 1.5 — Hands-on: Investigando comportamento operacional com múltiplos sinais
==================================================================================
EXERCÍCIO PRÁTICO — Aula 1

Neste hands-on você vai investigar um incidente real combinando
todas as técnicas aprendidas na Aula 1:
  1. Comparar visão black-box vs. observabilidade (1.1)
  2. Correlacionar métricas, logs e traces (1.2)
  3. Usar contexto operacional de deploys (1.3)
  4. Entender o fluxo de dados no padrão OpenTelemetry (1.4)

Cenário:
  Terça-feira às 14:22 UTC, o dashboard de SLOs acusa breach
  no serviço de checkout. Error budget consumido em 45 minutos.
  Sua missão: identificar a causa raiz usando observabilidade moderna.

Execute:
  python multi_signal_investigation.py
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class SignalType(str, Enum):
    METRIC = "METRIC"
    LOG    = "LOG"
    TRACE  = "TRACE"
    EVENT  = "EVENT"


class Severity(str, Enum):
    INFO     = "INFO"
    WARN     = "WARN"
    ERROR    = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class Signal:
    """Sinal de observabilidade unificado."""
    signal_type: SignalType
    service: str
    message: str
    timestamp: datetime
    severity: Severity = Severity.INFO
    trace_id: Optional[str] = None
    value: Optional[float] = None
    metadata: dict = field(default_factory=dict)

    def __str__(self) -> str:
        icon = {"METRIC": "📈", "LOG": "📝", "TRACE": "🔗", "EVENT": "🏷️"}[self.signal_type.value]
        sev_icon = {"INFO": "  ", "WARN": "⚠️", "ERROR": "❌", "CRITICAL": "🔴"}[self.severity.value]
        trace = f" [trace:{self.trace_id[:8]}]" if self.trace_id else ""
        return (
            f"  {icon} [{self.timestamp.strftime('%H:%M:%S')}] {sev_icon} "
            f"{self.service}: {self.message}{trace}"
        )


@dataclass
class Investigation:
    """Resultado da investigação com múltiplos sinais."""
    signals_total: int
    signals_correlated: int
    root_cause_service: str
    root_cause_description: str
    change_correlation: Optional[str]
    affected_services: list[str]
    impact_score: float
    recommended_actions: list[str]


# ---------------------------------------------------------------------------
# Cenário do exercício
# ---------------------------------------------------------------------------

def load_scenario() -> list[Signal]:
    """Carrega os sinais do incidente. Em produção, viriam de OTel Collector."""
    base = datetime(2024, 8, 13, 14, 22, 0)
    trace_id = "e7f8a9b0c1d2e3f4a5b6c7d8"

    return [
        # Deploy event (contexto operacional)
        Signal(SignalType.EVENT, "deploy-controller",
               "Deploy inventory-service v4.2.0 → v4.3.0 (new gRPC client)",
               base - timedelta(minutes=12), Severity.INFO,
               metadata={"version": "v4.3.0", "commit": "9a8b7c6", "author": "backend-squad"}),

        # Primeiros sinais da falha
        Signal(SignalType.METRIC, "inventory-service",
               "grpc_client_errors_total rate=0.42/s (baseline: 0.001/s)",
               base, Severity.ERROR, value=0.42,
               metadata={"metric": "grpc_client_errors_total"}),
        Signal(SignalType.LOG, "inventory-service",
               "ERROR: gRPC deadline exceeded calling warehouse-service.GetStock()",
               base + timedelta(seconds=3), Severity.ERROR, trace_id=trace_id),
        Signal(SignalType.TRACE, "inventory-service",
               "GetProductAvailability → warehouse-service.GetStock() DEADLINE_EXCEEDED (5001ms)",
               base + timedelta(seconds=5), Severity.ERROR, trace_id=trace_id,
               metadata={"span_duration_ms": 5001, "grpc_status": "DEADLINE_EXCEEDED"}),

        # Propagação
        Signal(SignalType.LOG, "checkout-service",
               "WARN: inventory check failed — proceeding with stale cache",
               base + timedelta(seconds=10), Severity.WARN, trace_id=trace_id),
        Signal(SignalType.METRIC, "checkout-service",
               "checkout_error_rate=0.18 (SLO threshold: 0.01)",
               base + timedelta(seconds=15), Severity.ERROR, value=0.18,
               metadata={"slo_status": "BREACHED"}),
        Signal(SignalType.LOG, "checkout-service",
               "ERROR: Stale cache returned oversold item SKU-7891",
               base + timedelta(seconds=20), Severity.ERROR, trace_id=trace_id),
        Signal(SignalType.METRIC, "api-gateway",
               "http_5xx_rate=0.12 on /api/checkout endpoint",
               base + timedelta(seconds=25), Severity.WARN, value=0.12),

        # Sinais da causa raiz profunda
        Signal(SignalType.LOG, "inventory-service",
               "DEBUG: gRPC channel using new TLS config from v4.3.0",
               base + timedelta(seconds=2), Severity.INFO, trace_id=trace_id,
               metadata={"config": "grpc.tls.cert_path=/etc/ssl/new-cert.pem"}),
        Signal(SignalType.LOG, "warehouse-service",
               "WARN: TLS handshake failed — peer certificate mismatch",
               base + timedelta(seconds=4), Severity.WARN, trace_id=trace_id,
               metadata={"expected_cn": "inventory.internal", "received_cn": "inventory-dev.internal"}),
        Signal(SignalType.METRIC, "warehouse-service",
               "grpc_server_handled_total{code=UNAVAILABLE} spike to 340/min",
               base + timedelta(seconds=8), Severity.ERROR, value=340),

        # Serviços não afetados (ruído a ser filtrado)
        Signal(SignalType.LOG, "notification-service",
               "INFO: Email batch completed — 2341 emails sent",
               base + timedelta(minutes=2), Severity.INFO),
        Signal(SignalType.METRIC, "analytics-service",
               "etl_job_duration_seconds=125 (normal range)",
               base + timedelta(minutes=3), Severity.INFO, value=125),
    ]


def correlate_signals(signals: list[Signal]) -> dict:
    """
    PASSO 1: Agrupa sinais por trace_id e serviço afetado.
    """
    correlated = {"by_trace": {}, "by_service": {}, "events": [], "noise": []}

    for s in signals:
        if s.signal_type == SignalType.EVENT:
            correlated["events"].append(s)
        elif s.trace_id:
            correlated["by_trace"].setdefault(s.trace_id, []).append(s)
        elif s.severity in (Severity.ERROR, Severity.CRITICAL, Severity.WARN):
            correlated["by_service"].setdefault(s.service, []).append(s)
        else:
            correlated["noise"].append(s)

    return correlated


def identify_root_cause(correlated: dict) -> Investigation:
    """
    PASSO 2: Analisa sinais correlacionados para identificar causa raiz.
    """
    trace_signals = []
    for sigs in correlated["by_trace"].values():
        trace_signals.extend(sigs)

    # Encontrar o serviço com erro mais profundo na cadeia
    error_services = {}
    for s in trace_signals:
        if s.severity in (Severity.ERROR, Severity.WARN):
            error_services.setdefault(s.service, []).append(s)

    # O warehouse-service reporta TLS mismatch — causa raiz técnica
    # O inventory-service v4.3.0 introduziu o bug — causa raiz operacional

    all_signals = []
    for sigs in correlated.values():
        if isinstance(sigs, list):
            all_signals.extend(sigs)
        elif isinstance(sigs, dict):
            for v in sigs.values():
                all_signals.extend(v)

    deploy_event = correlated["events"][0] if correlated["events"] else None

    affected = list(error_services.keys())

    return Investigation(
        signals_total=len(all_signals),
        signals_correlated=len(trace_signals),
        root_cause_service="inventory-service",
        root_cause_description=(
            "Deploy v4.3.0 introduziu novo cliente gRPC com certificado TLS incorreto "
            "(CN=inventory-dev.internal ao invés de inventory.internal). "
            "warehouse-service rejeita o handshake TLS, causando DEADLINE_EXCEEDED."
        ),
        change_correlation=(
            f"Deploy inventory-service {deploy_event.metadata.get('version', '?')} "
            f"(commit: {deploy_event.metadata.get('commit', '?')}) "
            f"às {deploy_event.timestamp.strftime('%H:%M')} — "
            f"12 minutos antes do início dos erros"
        ) if deploy_event else None,
        affected_services=affected,
        impact_score=82.0,
        recommended_actions=[
            "[IMEDIATO] Rollback inventory-service para v4.2.0",
            "[IMEDIATO] Verificar certificado TLS em /etc/ssl/new-cert.pem",
            "[CURTO]    Corrigir CN do certificado: inventory-dev.internal → inventory.internal",
            "[MÉDIO]    Adicionar validação de TLS no pipeline de CI/CD",
            "[LONGO]    Implementar canary deploy com verificação de gRPC health",
        ],
    )


def run_investigation() -> None:
    print("=" * 70)
    print("🚨 HANDS-ON: Investigação com Múltiplos Sinais")
    print("   Curso 3 — Observabilidade Inteligente — Aula 1")
    print("=" * 70)
    print(f"\n  ⏰ Terça-feira 14:22 UTC — SLO breach detectado no checkout")
    print(f"  📊 Error budget consumido: 78% em 45 minutos\n")
    time.sleep(0.3)

    # Carregar cenário
    signals = load_scenario()
    print(f"  📥 {len(signals)} sinais recebidos de múltiplas fontes (OTel Collector)")
    time.sleep(0.3)

    # PASSO 1: Listar todos os sinais
    print("\n" + "─" * 70)
    print("PASSO 1/4 — Sinais recebidos (timeline)")
    print("─" * 70)
    for s in sorted(signals, key=lambda x: x.timestamp):
        print(s)
    time.sleep(0.3)

    # PASSO 2: Correlação
    print("\n" + "─" * 70)
    print("PASSO 2/4 — Correlação automática de sinais")
    print("─" * 70)
    correlated = correlate_signals(signals)
    print(f"\n  Sinais correlacionados por trace : {sum(len(v) for v in correlated['by_trace'].values())}")
    print(f"  Sinais por serviço (sem trace)   : {sum(len(v) for v in correlated['by_service'].values())}")
    print(f"  Eventos de contexto (deploys)    : {len(correlated['events'])}")
    print(f"  Ruído filtrado                   : {len(correlated['noise'])}")

    for trace_id, sigs in correlated["by_trace"].items():
        print(f"\n  🔗 Trace {trace_id[:8]}... ({len(sigs)} sinais):")
        for s in sigs:
            print(f"    {s}")
    time.sleep(0.3)

    # PASSO 3: Identificação da causa raiz
    print("\n" + "─" * 70)
    print("PASSO 3/4 — Identificação da causa raiz")
    print("─" * 70)
    investigation = identify_root_cause(correlated)
    print(f"""
  🎯 CAUSA RAIZ IDENTIFICADA
  ─────────────────────────────────────────────
  Serviço         : {investigation.root_cause_service}
  Descrição       : {investigation.root_cause_description}
  Correlação      : {investigation.change_correlation}
  Serviços afetados: {', '.join(investigation.affected_services)}
  Impact score    : {investigation.impact_score}/100
    """)
    time.sleep(0.3)

    # PASSO 4: Relatório final
    print("─" * 70)
    print("PASSO 4/4 — Relatório de investigação")
    print("─" * 70)
    print(f"""
  📋 SUMÁRIO DO INCIDENTE
  ─────────────────────────────────────────────
  Início detectado   : 14:22 UTC
  Sinais recebidos   : {investigation.signals_total}
  Sinais correlacionados: {investigation.signals_correlated}
  Ruído filtrado     : {len(correlated['noise'])} sinais irrelevantes

  ✅ AÇÕES RECOMENDADAS (em ordem de prioridade)
  ─────────────────────────────────────────────""")
    for i, action in enumerate(investigation.recommended_actions, 1):
        print(f"  {i}. {action}")

    noise_pct = len(correlated['noise']) / investigation.signals_total * 100
    print(f"""
  📊 MÉTRICAS DO EXERCÍCIO
  ─────────────────────────────────────────────
  Redução de ruído   : {noise_pct:.0f}% dos sinais eram irrelevantes
  Técnica usada      : Correlação por trace_id + contexto de deploy
  Tempo de diagnóstico: ~4 min (vs. 45+ min com ferramentas isoladas)
    """)

    print("=" * 70)
    print("🎓 FIM DO HANDS-ON — AULA 1 CONCLUÍDA!")
    print("=" * 70)
    print("""
  Você aprendeu a:
  ✔ Diferenciar monitoramento black-box de observabilidade moderna
  ✔ Correlacionar métricas, logs e traces via trace_id
  ✔ Usar contexto operacional (deploys) para identificar regressões
  ✔ Entender o papel do OpenTelemetry na padronização de telemetria
  ✔ Investigar um incidente real com sinais múltiplos correlacionados

  Próxima aula: Tendências e comportamento operacional →
    """)


if __name__ == "__main__":
    run_investigation()
