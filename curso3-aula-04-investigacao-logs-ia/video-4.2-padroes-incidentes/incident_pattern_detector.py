"""
Vídeo 4.2 — Identificando padrões recorrentes em incidentes
=============================================================
Demonstra agrupamento estatístico de incidentes históricos para
mapear tendências invisíveis e causas raízes recorrentes.

Conceitos demonstrados:
- Clustering de incidentes por características comuns
- Detecção de causas raízes recorrentes
- Análise de frequência e sazonalidade de falhas
- Priorização de investimentos em confiabilidade
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class HistoricalIncident:
    id: str
    title: str
    severity: str
    date: datetime
    duration_minutes: int
    root_cause_category: str
    affected_service: str
    tags: list[str] = field(default_factory=list)


def generate_incident_history() -> list[HistoricalIncident]:
    """Gera 6 meses de histórico de incidentes com padrões ocultos."""
    base = datetime(2024, 1, 1)
    incidents = [
        # Cluster 1: Database connection pool (recorrente!)
        HistoricalIncident("INC-001", "DB connection pool exhausted", "SEV-1", base + timedelta(days=12), 45, "database", "user-service", ["connection-pool", "capacity"]),
        HistoricalIncident("INC-008", "DB connections maxed out", "SEV-1", base + timedelta(days=45), 38, "database", "checkout-service", ["connection-pool", "capacity"]),
        HistoricalIncident("INC-015", "PostgreSQL max_connections reached", "SEV-2", base + timedelta(days=78), 25, "database", "auth-service", ["connection-pool", "config"]),
        HistoricalIncident("INC-022", "DB pool saturation during peak", "SEV-1", base + timedelta(days=112), 52, "database", "product-service", ["connection-pool", "capacity"]),
        HistoricalIncident("INC-028", "Connection leak in user-service", "SEV-2", base + timedelta(days=140), 30, "database", "user-service", ["connection-pool", "bug"]),
        # Cluster 2: Certificate expiration
        HistoricalIncident("INC-004", "TLS cert expired on api-gw", "SEV-1", base + timedelta(days=25), 55, "certificate", "api-gateway", ["tls", "expiration"]),
        HistoricalIncident("INC-018", "Internal cert expired", "SEV-2", base + timedelta(days=88), 40, "certificate", "payment-service", ["tls", "internal"]),
        HistoricalIncident("INC-030", "Wildcard cert not renewed", "SEV-1", base + timedelta(days=155), 65, "certificate", "api-gateway", ["tls", "automation"]),
        # Cluster 3: Deployment related
        HistoricalIncident("INC-003", "Bad deploy caused 5xx spike", "SEV-2", base + timedelta(days=20), 20, "deployment", "checkout-service", ["deploy", "regression"]),
        HistoricalIncident("INC-010", "Config change broke auth", "SEV-1", base + timedelta(days=55), 35, "deployment", "auth-service", ["config", "regression"]),
        HistoricalIncident("INC-019", "Canary deploy not caught", "SEV-2", base + timedelta(days=92), 18, "deployment", "product-service", ["deploy", "canary"]),
        HistoricalIncident("INC-025", "Feature flag rollout issue", "SEV-3", base + timedelta(days=130), 15, "deployment", "frontend", ["feature-flag", "rollout"]),
        # Cluster 4: Capacity / scaling
        HistoricalIncident("INC-006", "CPU spike on Black Friday", "SEV-1", base + timedelta(days=35), 90, "capacity", "api-gateway", ["cpu", "scaling"]),
        HistoricalIncident("INC-014", "Disk full on log volume", "SEV-2", base + timedelta(days=72), 28, "capacity", "log-collector", ["disk", "logs"]),
        HistoricalIncident("INC-027", "OOM killer on analytics", "SEV-2", base + timedelta(days=135), 22, "capacity", "analytics", ["memory", "oom"]),
        # Isolated
        HistoricalIncident("INC-009", "DNS resolution failure", "SEV-1", base + timedelta(days=48), 42, "network", "api-gateway", ["dns"]),
        HistoricalIncident("INC-020", "Third-party API outage", "SEV-2", base + timedelta(days=95), 120, "external", "payment-service", ["third-party"]),
    ]
    return incidents


def cluster_incidents(incidents: list[HistoricalIncident]) -> dict[str, list[HistoricalIncident]]:
    """Agrupa incidentes por categoria de causa raiz."""
    clusters: dict[str, list[HistoricalIncident]] = {}
    for inc in incidents:
        clusters.setdefault(inc.root_cause_category, []).append(inc)
    return clusters


def analyze_patterns(clusters: dict[str, list[HistoricalIncident]]) -> None:
    """Analisa padrões recorrentes nos clusters de incidentes."""
    print(f"\n{'─' * 70}")
    print("📊 ANÁLISE DE PADRÕES RECORRENTES")
    print(f"{'─' * 70}")

    # Ordenar por frequência
    sorted_clusters = sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)

    for category, incs in sorted_clusters:
        count = len(incs)
        avg_duration = sum(i.duration_minutes for i in incs) / count
        sev1_count = sum(1 for i in incs if i.severity == "SEV-1")
        services = Counter(i.affected_service for i in incs)
        tags = Counter(t for i in incs for t in i.tags)

        bar = "█" * count
        print(f"\n  🔍 {category.upper()} ({count} incidentes)")
        print(f"     Frequência : {bar} ({count})")
        print(f"     Duração média: {avg_duration:.0f} min")
        print(f"     SEV-1 count : {sev1_count}")
        print(f"     Serviços    : {dict(services.most_common(3))}")
        print(f"     Tags comuns : {dict(tags.most_common(3))}")

        # Intervalo médio entre incidentes
        dates = sorted(i.date for i in incs)
        if len(dates) > 1:
            intervals = [(dates[j] - dates[j - 1]).days for j in range(1, len(dates))]
            avg_interval = sum(intervals) / len(intervals)
            print(f"     Intervalo médio: {avg_interval:.0f} dias")
            next_predicted = dates[-1] + timedelta(days=avg_interval)
            print(f"     Próximo previsto: ~{next_predicted.strftime('%d/%m/%Y')}")


def run_demo() -> None:
    print("=" * 70)
    print("🔍 Demo: Identificando Padrões Recorrentes em Incidentes")
    print("   Curso 3 — Observabilidade Inteligente")
    print("=" * 70)

    incidents = generate_incident_history()

    print(f"\n  📋 Analisando {len(incidents)} incidentes dos últimos 6 meses...")

    clusters = cluster_incidents(incidents)
    analyze_patterns(clusters)

    # Top investimentos
    print(f"\n{'=' * 70}")
    print("💡 RECOMENDAÇÕES DE INVESTIMENTO EM CONFIABILIDADE")
    print(f"{'=' * 70}")

    ranked = sorted(clusters.items(), key=lambda x: (
        len(x[1]) * sum(1 for i in x[1] if i.severity == "SEV-1") + len(x[1])
    ), reverse=True)

    for i, (cat, incs) in enumerate(ranked[:3], 1):
        total_downtime = sum(inc.duration_minutes for inc in incs)
        print(f"\n  #{i} {cat.upper()}")
        print(f"     {len(incs)} incidentes | {total_downtime} min de downtime total")
        if cat == "database":
            print(f"     → Implementar PgBouncer + alertas de pool + limites por serviço")
        elif cat == "certificate":
            print(f"     → Automação de cert-manager + alerta de renovação + canary TLS")
        elif cat == "deployment":
            print(f"     → Canary deploys obrigatórios + rollback automático + feature flags")

    print("\n" + "=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  A análise de padrões revela que a maioria dos incidentes pertence
  a poucos clusters de causa raiz. Investir nos top 3 clusters
  pode eliminar 70%+ dos incidentes recorrentes.

  Na Aula 4.3, veremos como agrupar logs automaticamente para
  isolar exceções em grandes volumes de dados.
    """)


if __name__ == "__main__":
    run_demo()
