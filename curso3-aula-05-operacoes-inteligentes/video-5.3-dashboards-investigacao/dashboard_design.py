"""
Vídeo 5.3 — Dashboards orientados à investigação operacional
==============================================================
Demonstra princípios de design de dashboards que otimizam o fluxo
visual de troubleshooting com hierarquia USE/RED e drill-down.

Conceitos demonstrados:
- Método USE (Utilization, Saturation, Errors) para infra
- Método RED (Rate, Errors, Duration) para serviços
- Hierarquia visual: overview → service → detail
- Anti-patterns comuns em dashboards
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DashboardPanel:
    title: str
    metric_type: str
    query: str
    visualization: str  # timeseries, gauge, stat, table, heatmap
    position: tuple[int, int]  # (row, col)
    size: tuple[int, int]  # (width, height)
    thresholds: dict = field(default_factory=dict)


@dataclass
class Dashboard:
    title: str
    audience: str
    panels: list[DashboardPanel]
    drill_down_to: str | None = None


def create_overview_dashboard() -> Dashboard:
    """Dashboard Level 0: Visão geral do sistema."""
    return Dashboard(
        title="🏠 System Overview",
        audience="SRE On-Call",
        drill_down_to="Service Detail",
        panels=[
            DashboardPanel("System Health Score", "composite", "min(slo_compliance)", "stat", (0, 0), (4, 2), {"red": 0.95, "yellow": 0.99}),
            DashboardPanel("Active Incidents", "count", "count(active_incidents)", "stat", (0, 4), (2, 2)),
            DashboardPanel("Error Budget Burn Rate", "rate", "error_budget_burn_rate", "gauge", (0, 6), (2, 2)),
            DashboardPanel("Top 5 Error Services", "table", "topk(5, error_rate)", "table", (2, 0), (4, 3)),
            DashboardPanel("Request Rate (global)", "rate", "sum(http_requests_total)", "timeseries", (2, 4), (4, 3)),
            DashboardPanel("P99 Latency by Service", "latency", "histogram_quantile(0.99, ...)", "timeseries", (5, 0), (8, 3)),
            DashboardPanel("Recent Deploys", "events", "deploy_events{status='completed'}", "table", (5, 4), (4, 3)),
        ],
    )


def create_service_dashboard() -> Dashboard:
    """Dashboard Level 1: Detalhe de um serviço (RED method)."""
    return Dashboard(
        title="🔍 Service Detail — checkout-service",
        audience="Service Owner",
        drill_down_to="Trace Detail",
        panels=[
            DashboardPanel("Rate (req/s)", "rate", "rate(http_requests_total{service='checkout'}[5m])", "timeseries", (0, 0), (4, 2)),
            DashboardPanel("Error Rate (%)", "percentage", "rate(http_errors_total[5m]) / rate(http_requests_total[5m])", "timeseries", (0, 4), (4, 2)),
            DashboardPanel("Duration (p50/p95/p99)", "latency", "histogram_quantile({0.5,0.95,0.99}, ...)", "timeseries", (0, 8), (4, 2)),
            DashboardPanel("Error Rate by Endpoint", "breakdown", "rate(errors) by endpoint", "timeseries", (2, 0), (6, 3)),
            DashboardPanel("Upstream Dependencies", "health", "dependency_health{service='checkout'}", "table", (2, 6), (6, 3)),
            DashboardPanel("Resource Usage (USE)", "utilization", "container_cpu/memory/network", "timeseries", (5, 0), (8, 4)),
            DashboardPanel("Recent Logs (ERROR)", "logs", "logs{service='checkout', level='ERROR'}", "table", (5, 8), (4, 4)),
        ],
    )


def create_infra_dashboard() -> Dashboard:
    """Dashboard de infraestrutura (USE method)."""
    return Dashboard(
        title="🖥️ Infrastructure — USE Method",
        audience="Platform Engineer",
        panels=[
            DashboardPanel("CPU Utilization", "utilization", "container_cpu_usage_seconds_total", "heatmap", (0, 0), (6, 3)),
            DashboardPanel("Memory Saturation", "saturation", "container_memory_working_set / limit", "gauge", (0, 6), (3, 3)),
            DashboardPanel("Disk I/O Errors", "errors", "node_disk_io_errors_total", "timeseries", (0, 9), (3, 3)),
            DashboardPanel("Network Utilization", "utilization", "node_network_transmit_bytes_total", "timeseries", (3, 0), (6, 3)),
            DashboardPanel("Pod Saturation", "saturation", "kube_pod_status_phase", "table", (3, 6), (6, 3)),
        ],
    )


def print_dashboard(db: Dashboard) -> None:
    """Renderiza uma representação ASCII do dashboard."""
    print(f"\n  📊 {db.title}")
    print(f"     Audiência: {db.audience}")
    if db.drill_down_to:
        print(f"     Drill-down → {db.drill_down_to}")
    print()

    for panel in db.panels:
        row, col = panel.position
        viz_icons = {
            "timeseries": "📈", "gauge": "🎯", "stat": "🔢",
            "table": "📋", "heatmap": "🌡️",
        }
        icon = viz_icons.get(panel.visualization, "📊")
        print(f"     {icon} [{panel.visualization:11}] {panel.title}")
        print(f"        Query: {panel.query[:55]}...")
        if panel.thresholds:
            print(f"        Thresholds: {panel.thresholds}")


def print_anti_patterns() -> None:
    """Mostra anti-patterns comuns em dashboards."""
    print(f"\n{'─' * 70}")
    print("❌ ANTI-PATTERNS COMUNS EM DASHBOARDS")
    print(f"{'─' * 70}")

    anti_patterns = [
        ("Dashboard de 50+ painéis", "Ninguém sabe para onde olhar primeiro",
         "Máximo 8-12 painéis por dashboard, use drill-down"),
        ("Apenas métricas cruas", "CPU 78% — é bom ou ruim? Ninguém sabe",
         "Adicionar thresholds visuais e contexto (SLO, baseline)"),
        ("Sem hierarquia", "Overview e detalhe no mesmo nível",
         "L0 (overview) → L1 (serviço) → L2 (trace/log)"),
        ("Métricas sem ação", "Painéis bonitos que ninguém usa para debugar",
         "Todo painel deve responder: O que faço quando está vermelho?"),
        ("Dashboard estático", "Mesma view para on-call e para CTO",
         "Audiências diferentes = dashboards diferentes"),
    ]

    for name, problem, solution in anti_patterns:
        print(f"\n  ❌ {name}")
        print(f"     Problema: {problem}")
        print(f"     ✅ Fix  : {solution}")


def run_demo() -> None:
    print("=" * 70)
    print("📊 Demo: Dashboards Orientados à Investigação")
    print("   Curso 3 — Observabilidade Inteligente")
    print("=" * 70)

    # Hierarquia
    print(f"\n{'─' * 70}")
    print("🏗️  HIERARQUIA DE DASHBOARDS (drill-down)")
    print(f"{'─' * 70}")
    print("""
  Level 0: System Overview     ← "Tudo está OK?"
      │
      ├── Level 1: Service Detail  ← "Qual serviço está com problema?"
      │       │
      │       └── Level 2: Trace/Log  ← "Qual a causa raiz?"
      │
      └── Level 1: Infrastructure  ← "É problema de infra?"
    """)

    # Dashboards
    dashboards = [
        create_overview_dashboard(),
        create_service_dashboard(),
        create_infra_dashboard(),
    ]

    print(f"{'─' * 70}")
    print("📋 DASHBOARDS PROPOSTOS (RED + USE methods)")
    print(f"{'─' * 70}")

    for db in dashboards:
        print_dashboard(db)

    # Anti-patterns
    print_anti_patterns()

    # Princípios
    print(f"\n{'=' * 70}")
    print("📌 PRINCÍPIOS DE DESIGN DE DASHBOARDS SRE")
    print(f"{'=' * 70}")
    print("""
  1. HIERARQUIA: Overview → Service → Detail (drill-down natural)
  2. RED para serviços: Rate, Errors, Duration (o que o usuário sente)
  3. USE para infra: Utilization, Saturation, Errors (recursos)
  4. AUDIÊNCIA: Dashboard diferente para cada persona
  5. AÇÃO: Todo painel deve ter um "e daí?" claro
  6. CONTEXTO: Incluir deploys, SLOs e baselines como referência
  7. PARCIMÔNIA: 8-12 painéis max por dashboard

  Na Aula 5.4, veremos como reduzir a carga cognitiva em
  situações de crise usando esses princípios.
    """)


if __name__ == "__main__":
    run_demo()
