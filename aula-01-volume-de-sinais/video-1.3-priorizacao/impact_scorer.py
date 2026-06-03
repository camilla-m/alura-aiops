"""
Vídeo 1.3 — Priorização operacional baseada em contexto
========================================================
Demonstra como calcular o impacto real de uma falha usando
contexto arquitetural (dependências, usuários afetados, SLOs)
para priorizar automaticamente a triagem de incidentes.

Conceitos demonstrados:
- Impact Score baseado em blast radius (serviços afetados)
- Ponderação por criticidade de negócio
- Geração de triage report automatizado
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Modelo de serviço com contexto de negócio
# ---------------------------------------------------------------------------

@dataclass
class ServiceProfile:
    """Perfil de um serviço com seu contexto de negócio e criticidade."""
    name: str
    tier: int               # 1 = crítico, 2 = importante, 3 = auxiliar
    users_affected: int     # usuários impactados em caso de falha
    revenue_impact: float   # impacto financeiro por minuto de indisponibilidade (R$)
    slo_target: float       # SLO alvo (0-1), ex: 0.999 = 99.9%
    current_slo: float      # SLO atual medido
    dependencies: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Catálogo de serviços (contexto arquitetural)
# ---------------------------------------------------------------------------

SERVICE_CATALOG: dict[str, ServiceProfile] = {
    "database": ServiceProfile(
        name="database",
        tier=1, users_affected=50_000, revenue_impact=5000.0,
        slo_target=0.9999, current_slo=0.9997,
        dependencies=[],
    ),
    "cache": ServiceProfile(
        name="cache",
        tier=2, users_affected=50_000, revenue_impact=500.0,
        slo_target=0.999, current_slo=0.9992,
        dependencies=["database"],
    ),
    "auth-service": ServiceProfile(
        name="auth-service",
        tier=1, users_affected=50_000, revenue_impact=3000.0,
        slo_target=0.9995, current_slo=0.9994,
        dependencies=["database", "cache"],
    ),
    "payment-service": ServiceProfile(
        name="payment-service",
        tier=1, users_affected=12_000, revenue_impact=8000.0,
        slo_target=0.9999, current_slo=0.9998,
        dependencies=["auth-service"],
    ),
    "product-service": ServiceProfile(
        name="product-service",
        tier=2, users_affected=40_000, revenue_impact=2000.0,
        slo_target=0.999, current_slo=0.9985,
        dependencies=["database", "cache"],
    ),
    "api-gateway": ServiceProfile(
        name="api-gateway",
        tier=1, users_affected=50_000, revenue_impact=4000.0,
        slo_target=0.9999, current_slo=0.9996,
        dependencies=["auth-service", "product-service"],
    ),
    "notification-service": ServiceProfile(
        name="notification-service",
        tier=3, users_affected=5_000, revenue_impact=100.0,
        slo_target=0.99, current_slo=0.991,
        dependencies=["database"],
    ),
    "analytics": ServiceProfile(
        name="analytics",
        tier=3, users_affected=0, revenue_impact=50.0,
        slo_target=0.95, current_slo=0.952,
        dependencies=["database"],
    ),
}


# ---------------------------------------------------------------------------
# Motor de scoring de impacto
# ---------------------------------------------------------------------------

@dataclass
class IncidentTriage:
    """Resultado da triagem de um incidente."""
    service: str
    impact_score: float        # 0-100
    blast_radius: int          # número de serviços afetados
    users_at_risk: int
    revenue_risk_per_min: float
    slo_burn_rate: float       # taxa de consumo do error budget
    priority: str              # P1, P2, P3
    recommended_action: str


def get_downstream_services(service_name: str) -> list[str]:
    """Retorna todos os serviços que dependem (direta ou indiretamente) do serviço dado."""
    downstream = []
    for svc_name, profile in SERVICE_CATALOG.items():
        if service_name in _get_all_deps(svc_name) and svc_name != service_name:
            downstream.append(svc_name)
    return downstream


def _get_all_deps(service_name: str, visited: Optional[set] = None) -> set[str]:
    """Resolução recursiva de dependências."""
    if visited is None:
        visited = set()
    profile = SERVICE_CATALOG.get(service_name)
    if not profile:
        return visited
    for dep in profile.dependencies:
        if dep not in visited:
            visited.add(dep)
            _get_all_deps(dep, visited)
    return visited


def calculate_impact_score(service_name: str) -> IncidentTriage:
    """
    Calcula o impact score de uma falha em um serviço específico.
    
    Fórmula:
        score = (tier_weight × 40) + (users_factor × 30) + (revenue_factor × 20) + (slo_factor × 10)
    """
    profile = SERVICE_CATALOG.get(service_name)
    if not profile:
        raise ValueError(f"Serviço '{service_name}' não encontrado no catálogo.")

    downstream = get_downstream_services(service_name)
    all_affected = [service_name] + downstream

    # Usuários e receita acumulados (impacto cascata)
    total_users = max(p.users_affected for name in all_affected if (p := SERVICE_CATALOG.get(name)))
    total_revenue = sum(
        SERVICE_CATALOG[name].revenue_impact
        for name in all_affected
        if name in SERVICE_CATALOG
    )

    # Fatores normalizados (0-1)
    tier_weight = (4 - profile.tier) / 3            # tier 1 → 1.0, tier 3 → 0.33
    users_factor = min(total_users / 50_000, 1.0)
    revenue_factor = min(total_revenue / 10_000, 1.0)
    slo_gap = max(profile.slo_target - profile.current_slo, 0)
    slo_factor = min(slo_gap / 0.001, 1.0)          # normalizado por 0.1% de gap

    score = (tier_weight * 40) + (users_factor * 30) + (revenue_factor * 20) + (slo_factor * 10)

    # Determina prioridade
    if score >= 75:
        priority = "P1 — Crítico"
        action = "Acionar war room imediatamente. Notificar stakeholders."
    elif score >= 50:
        priority = "P2 — Alto"
        action = "Investigar em até 15 min. Escalar se não resolvido em 30 min."
    elif score >= 30:
        priority = "P3 — Médio"
        action = "Investigar no próximo ciclo. Monitorar evolução."
    else:
        priority = "P4 — Baixo"
        action = "Registrar e monitorar. Resolver durante horário comercial."

    # SLO burn rate
    error_budget_remaining = profile.slo_target - profile.current_slo
    burn_rate = slo_gap / max(error_budget_remaining, 0.0001) if error_budget_remaining > 0 else 99.0

    return IncidentTriage(
        service=service_name,
        impact_score=round(score, 1),
        blast_radius=len(all_affected),
        users_at_risk=total_users,
        revenue_risk_per_min=total_revenue,
        slo_burn_rate=burn_rate,
        priority=priority,
        recommended_action=action,
    )


def triage_all_services() -> list[IncidentTriage]:
    """Calcula o impact score para todos os serviços e retorna ordenado por prioridade."""
    results = [calculate_impact_score(name) for name in SERVICE_CATALOG]
    return sorted(results, key=lambda t: t.impact_score, reverse=True)


def print_triage_report(triages: list[IncidentTriage]) -> None:
    """Exibe o relatório de triagem priorizado."""
    print("\n" + "=" * 70)
    print("🎯 RELATÓRIO DE TRIAGEM — PRIORIZAÇÃO POR IMPACTO")
    print("=" * 70)
    print(f"\n{'Serviço':<22} {'Score':>6} {'Prio':<12} {'Usuários':>10} {'R$/min':>10} {'Blast':>6}")
    print("─" * 70)

    for t in triages:
        print(
            f"  {t.service:<20} {t.impact_score:>6.1f} {t.priority[:12]:<12} "
            f"{t.users_at_risk:>10,} {t.revenue_risk_per_min:>9.0f}  {t.blast_radius:>5}"
        )

    print("\n" + "─" * 70)
    print("\n📋 DETALHES TOP-3 MAIS CRÍTICOS\n")
    for t in triages[:3]:
        print(f"  🔴 {t.service} — {t.priority}")
        print(f"     Score         : {t.impact_score}/100")
        print(f"     Serviços afetados : {t.blast_radius}")
        print(f"     Usuários em risco : {t.users_at_risk:,}")
        print(f"     Risco financeiro  : R$ {t.revenue_risk_per_min:,.0f}/min")
        print(f"     Ação recomendada  : {t.recommended_action}")
        print()


if __name__ == "__main__":
    print("🔬 Demo: Priorização Operacional Baseada em Contexto")
    print("     Nível 1 — AIOps & Automação de Incidentes")

    all_triages = triage_all_services()
    print_triage_report(all_triages)

    print("=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  Com o impact score calculado automaticamente, o time de operações
  sabe IMEDIATAMENTE qual incidente priorizar sem precisar investigar
  manualmente cada alerta.

  Plataformas de AIOps constroem esse score continuamente, considerando
  também dados históricos de MTTR e frequência de incidentes.
    """)
