"""
Vídeo 5.1 — Datadog, PagerDuty e observabilidade inteligente
=============================================================
Demonstra os recursos nativos de AIOps das principais
plataformas de observabilidade do mercado.

Conceitos demonstrados:
- Arquitetura de integração Datadog + PagerDuty
- Uso das APIs para automação de incidentes
- Datadog Watchdog (IA nativa de detecção de anomalias)
- Estrutura de notificação inteligente via PagerDuty
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Modelos de integração (simulam as APIs reais)
# ---------------------------------------------------------------------------

@dataclass
class DatadogMonitor:
    """Representa um monitor do Datadog."""
    monitor_id: int
    name: str
    query: str
    monitor_type: str       # metric | log | apm | composite
    is_ai_powered: bool     # usa Watchdog / Dynamic Baselines
    threshold_type: str     # static | dynamic | anomaly
    tags: list[str] = field(default_factory=list)
    notification_targets: list[str] = field(default_factory=list)


@dataclass
class PagerDutyService:
    """Representa um serviço no PagerDuty."""
    service_id: str
    name: str
    escalation_policy: str
    urgency: str             # high | low
    integration_type: str    # datadog | generic | email


@dataclass
class AIOpsWorkflow:
    """Fluxo de AIOps integrado Datadog → PagerDuty."""
    name: str
    trigger: str
    datadog_monitors: list[DatadogMonitor]
    pagerduty_service: PagerDutyService
    auto_remediation: bool
    ml_features: list[str]


# ---------------------------------------------------------------------------
# Demonstração de configuração de plataformas
# ---------------------------------------------------------------------------

DATADOG_MONITORS = [
    DatadogMonitor(
        monitor_id=12001,
        name="[AIOps] auth-service error rate anomaly",
        query="anomalies(avg:auth_service.error_rate{env:prod}, 'agile', 3)",
        monitor_type="metric",
        is_ai_powered=True,
        threshold_type="anomaly",
        tags=["env:prod", "service:auth-service", "tier:1", "team:sre"],
        notification_targets=["@pagerduty-sre-critical", "@slack-#incidents"],
    ),
    DatadogMonitor(
        monitor_id=12002,
        name="[AIOps] Database connection pool forecast",
        query="forecast(avg:postgresql.connections.active{env:prod}, 'linear', 1, interval='30m') > 90",
        monitor_type="metric",
        is_ai_powered=True,
        threshold_type="dynamic",
        tags=["env:prod", "service:database", "tier:1"],
        notification_targets=["@pagerduty-sre-high", "@slack-#alerts"],
    ),
    DatadogMonitor(
        monitor_id=12003,
        name="[AIOps] Watchdog anomaly detection — all services",
        query="watchdog",  # Watchdog é IA nativa do Datadog
        monitor_type="watchdog",
        is_ai_powered=True,
        threshold_type="dynamic",
        tags=["env:prod", "team:sre"],
        notification_targets=["@slack-#watchdog-alerts"],
    ),
    DatadogMonitor(
        monitor_id=12004,
        name="[Traditional] CPU usage > 85% static",
        query="avg(last_5m):avg:system.cpu.user{env:prod} > 85",
        monitor_type="metric",
        is_ai_powered=False,
        threshold_type="static",
        tags=["env:prod", "legacy"],
        notification_targets=["@slack-#alerts"],
    ),
]

PAGERDUTY_SERVICES = {
    "sre-critical": PagerDutyService(
        "SVC-001", "SRE On-Call — Critical",
        escalation_policy="EP-001: 5min → team lead → director",
        urgency="high",
        integration_type="datadog",
    ),
    "sre-high": PagerDutyService(
        "SVC-002", "SRE On-Call — High",
        escalation_policy="EP-002: 15min → team lead",
        urgency="high",
        integration_type="datadog",
    ),
}

AIOPS_WORKFLOW = AIOpsWorkflow(
    name="Incident Response — Auth Service",
    trigger="anomaly_detected OR error_rate > 80%",
    datadog_monitors=[DATADOG_MONITORS[0], DATADOG_MONITORS[1]],
    pagerduty_service=PAGERDUTY_SERVICES["sre-critical"],
    auto_remediation=True,
    ml_features=[
        "Watchdog — detecção automática de anomalias sem configuração",
        "Dynamic Baselines — thresholds adaptativos por sazonalidade",
        "Correlate Alerts — agrupamento automático de alertas relacionados",
        "Root Cause Analysis — sugestão de causa raiz com ML",
        "Forecast — previsão de esgotamento de recursos",
    ],
)


def print_platform_comparison() -> None:
    """Compara recursos de AIOps das plataformas líderes."""
    print("\n" + "=" * 70)
    print("🏆 COMPARATIVO: PLATAFORMAS LÍDERES DE AIOPS")
    print("=" * 70)

    platforms = [
        ("Datadog",    "Watchdog, Dynamic Baselines, Correlate Alerts, APM AI", "Alto", "⭐⭐⭐⭐⭐"),
        ("Dynatrace",  "Davis AI, Root Cause Analysis, Smartscape Topology",     "Alto", "⭐⭐⭐⭐⭐"),
        ("New Relic",  "AI Anomaly Detection, Incident Intelligence",            "Médio", "⭐⭐⭐⭐"),
        ("Grafana",    "Machine Learning Plugin, Anomaly Detection (OSS)",       "Baixo", "⭐⭐⭐"),
        ("Prometheus", "Alertmanager (sem AI nativa), requer integração",        "Baixo", "⭐⭐"),
    ]

    print(f"\n  {'Plataforma':<14} {'Recursos de IA':<45} {'Custo':<8} Rating")
    print("  " + "─" * 80)
    for name, features, cost, rating in platforms:
        print(f"  {name:<14} {features[:44]:<45} {cost:<8} {rating}")


def print_monitor_config() -> None:
    """Exibe configuração dos monitores AIOps."""
    print("\n" + "=" * 70)
    print("📊 MONITORES DATADOG CONFIGURADOS")
    print("=" * 70)

    ai_count = sum(1 for m in DATADOG_MONITORS if m.is_ai_powered)
    print(f"\n  Total de monitores  : {len(DATADOG_MONITORS)}")
    print(f"  Monitores com IA    : {ai_count} ({ai_count/len(DATADOG_MONITORS):.0%})")
    print(f"  Monitores estáticos : {len(DATADOG_MONITORS) - ai_count}")

    print(f"\n  {'ID':<8} {'Nome':<42} {'Tipo threshold':<12} IA?")
    print("  " + "─" * 75)
    for m in DATADOG_MONITORS:
        ai_badge = "🤖" if m.is_ai_powered else "📏"
        print(f"  {m.monitor_id:<8} {m.name[:40]:<42} {m.threshold_type:<12} {ai_badge}")


def print_workflow() -> None:
    """Exibe o fluxo integrado Datadog + PagerDuty."""
    print("\n" + "=" * 70)
    print("🔄 WORKFLOW INTEGRADO: DATADOG → PAGERDUTY → REMEDIAÇÃO")
    print("=" * 70)
    print(f"""
  Trigger      : {AIOPS_WORKFLOW.trigger}
  Serviço PD   : {AIOPS_WORKFLOW.pagerduty_service.name}
  Escalation   : {AIOPS_WORKFLOW.pagerduty_service.escalation_policy}
  Auto-remediar: {'✅ Sim' if AIOPS_WORKFLOW.auto_remediation else '❌ Não'}

  Funcionalidades de ML ativas:
  {chr(10).join('  • ' + f for f in AIOPS_WORKFLOW.ml_features)}
  """)

    print("  FLUXO COMPLETO:")
    print("""
  [Datadog Watchdog]
       │ anomalia detectada
       ▼
  [Correlate Alerts] ── agrupa sinais relacionados
       │
       ▼
  [Root Cause AI] ── sugere causa raiz
       │
       ▼
  [PagerDuty] ── notifica oncall com contexto
       │
       ▼
  [Self-Healing Engine] ── executa runbook (com guardrails)
       │
       ▼
  [Slack War Room] ── atualiza status automático
    """)


if __name__ == "__main__":
    print("🔬 Demo: Datadog, PagerDuty e Observabilidade Inteligente")
    print("     Nível 1 — AIOps & Automação de Incidentes")

    print_platform_comparison()
    print_monitor_config()
    print_workflow()
