"""
Vídeo 5.2 — Observabilidade apoiando tomada de decisão operacional
====================================================================
Demonstra como traduzir métricas técnicas (SLIs/SLOs) em impacto
de negócios compreensível pela gestão sênior e stakeholders.

Conceitos demonstrados:
- SLI/SLO/Error Budget como linguagem de negócios
- Conversão de latência em receita perdida
- Dashboard executivo vs. dashboard técnico
- Tomada de decisão baseada em dados observáveis
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class SLODefinition:
    name: str
    target: float
    window_days: int
    revenue_per_good_request: float  # R$ por requisição bem-sucedida

    @property
    def error_budget_pct(self) -> float:
        return (1 - self.target) * 100


@dataclass
class SLOStatus:
    slo: SLODefinition
    current_good_pct: float
    total_requests: int
    budget_consumed_pct: float
    budget_remaining_minutes: float
    revenue_at_risk: float


def calculate_slo_status(
    slo: SLODefinition,
    current_good_pct: float,
    total_requests: int,
    elapsed_days: int,
) -> SLOStatus:
    """Calcula o status atual de um SLO incluindo impacto financeiro."""
    window = slo.window_days
    error_budget = slo.error_budget_pct / 100

    current_errors = 1 - current_good_pct
    budget_consumed = current_errors / error_budget if error_budget > 0 else 999

    remaining_days = window - elapsed_days
    remaining_minutes = remaining_days * 24 * 60
    budget_remaining_minutes = remaining_minutes * (1 - budget_consumed) if budget_consumed < 1 else 0

    failed_requests = int(total_requests * (1 - current_good_pct))
    revenue_at_risk = failed_requests * slo.revenue_per_good_request

    return SLOStatus(
        slo=slo,
        current_good_pct=current_good_pct,
        total_requests=total_requests,
        budget_consumed_pct=budget_consumed * 100,
        budget_remaining_minutes=budget_remaining_minutes,
        revenue_at_risk=revenue_at_risk,
    )


def run_demo() -> None:
    print("=" * 70)
    print("📊 Demo: Observabilidade como Ferramenta de Decisão")
    print("   Curso 3 — Observabilidade Inteligente")
    print("=" * 70)

    slos = [
        SLODefinition("Checkout Availability", 0.999, 30, 12.50),
        SLODefinition("Search Latency (<500ms)", 0.995, 30, 0.08),
        SLODefinition("Payment Success Rate", 0.9995, 30, 45.00),
        SLODefinition("API Gateway Uptime", 0.9999, 30, 0.02),
    ]

    scenarios = [
        (0.9985, 2_500_000, 15),  # Checkout abaixo do SLO
        (0.997, 12_000_000, 15),  # Search ok
        (0.9988, 800_000, 15),    # Payment abaixo
        (0.99998, 50_000_000, 15), # Gateway ok
    ]

    # Visão técnica
    print(f"\n{'─' * 70}")
    print("🔧 VISÃO TÉCNICA (dashboard do SRE)")
    print(f"{'─' * 70}")

    statuses: list[SLOStatus] = []
    for slo, (good_pct, total, days) in zip(slos, scenarios):
        status = calculate_slo_status(slo, good_pct, total, days)
        statuses.append(status)

        icon = "🟢" if status.budget_consumed_pct < 80 else "🟡" if status.budget_consumed_pct < 100 else "🔴"
        print(f"\n  {icon} {slo.name}")
        print(f"     SLO target   : {slo.target:.4%}")
        print(f"     Atual        : {good_pct:.4%}")
        print(f"     Error budget : {status.budget_consumed_pct:.0f}% consumido")
        print(f"     Requisições  : {total:,}")

    # Visão executiva
    print(f"\n{'─' * 70}")
    print("📈 VISÃO EXECUTIVA (dashboard do CTO/VP)")
    print(f"{'─' * 70}")

    total_risk = sum(s.revenue_at_risk for s in statuses)

    print(f"\n  {'Serviço':<30} {'Saúde':<8} {'Budget':<12} {'Receita em Risco':<18}")
    print(f"  {'─' * 30} {'─' * 8} {'─' * 12} {'─' * 18}")

    for s in statuses:
        icon = "🟢" if s.budget_consumed_pct < 80 else "🟡" if s.budget_consumed_pct < 100 else "🔴"
        health = "OK" if s.budget_consumed_pct < 80 else "RISCO" if s.budget_consumed_pct < 100 else "BREACH"
        print(f"  {s.slo.name:<30} {icon} {health:<5} {s.budget_consumed_pct:>5.0f}%       R$ {s.revenue_at_risk:>10,.2f}")

    print(f"\n  {'─' * 70}")
    print(f"  {'TOTAL RECEITA EM RISCO':>50}  R$ {total_risk:>10,.2f}")

    # Tomada de decisão
    breached = [s for s in statuses if s.budget_consumed_pct >= 100]
    at_risk = [s for s in statuses if 80 <= s.budget_consumed_pct < 100]

    print(f"\n{'─' * 70}")
    print("🎯 DECISÕES BASEADAS EM DADOS")
    print(f"{'─' * 70}")

    if breached:
        print(f"\n  🔴 AÇÃO IMEDIATA NECESSÁRIA:")
        for s in breached:
            print(f"     • {s.slo.name}: Budget esgotado! Congelar deploys não-essenciais.")
            print(f"       Impacto: R$ {s.revenue_at_risk:,.2f} em receita comprometida")

    if at_risk:
        print(f"\n  🟡 MONITORAMENTO INTENSIVO:")
        for s in at_risk:
            print(f"     • {s.slo.name}: {100 - s.budget_consumed_pct:.0f}% de budget restante")
            print(f"       Ação: Reduzir risco com feature freeze parcial")

    print(f"""
  💡 LINGUAGEM DE NEGÓCIOS:

  Em vez de dizer:
    "p99 latency subiu para 800ms e error rate está em 0.15%"

  Diga:
    "Estamos perdendo R$ {total_risk:,.2f} por mês em receita devido
     a falhas no checkout e pagamento. Se não agirmos em 48h,
     o error budget da janela de 30 dias será totalmente consumido."

  → A segunda versão gera AÇÃO imediata da gestão.
    """)

    print("=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  SLOs são a ponte entre engenharia e negócios. Error budgets
  traduzem "percentuais de disponibilidade" em "dinheiro em risco",
  transformando conversas técnicas em decisões de negócio.

  Na Aula 5.3, veremos como desenhar dashboards que otimizam
  o fluxo de troubleshooting para diferentes audiências.
    """)


if __name__ == "__main__":
    run_demo()
