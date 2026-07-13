"""
Vídeo 3.4 — Alertas contextuais e investigação operacional
============================================================
Demonstra alertas complexos que consideram dependências de topologia
e estados lógicos para gerar alertas realmente acionáveis.

Conceitos demonstrados:
- Alertas com condições compostas (AND, OR, NOT)
- Supressão por dependência (se DB caiu, não alertar app)
- Alertas baseados em SLOs ao invés de métricas brutas
- Regras condicionais com contexto de infraestrutura
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class ServiceState(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"
    MAINTENANCE = "MAINTENANCE"


@dataclass
class ServiceTopology:
    """Topologia de serviços com dependências."""
    services: dict[str, list[str]]  # service -> dependencies
    states: dict[str, ServiceState]
    metrics: dict[str, dict[str, float]]  # service -> {metric: value}


@dataclass
class ContextualRule:
    """Regra de alerta contextual com condições compostas."""
    id: str
    name: str
    description: str
    conditions: list[str]  # Descrição das condições
    suppress_if: list[str]  # Condições de supressão

    def evaluate(self, topology: ServiceTopology) -> tuple[bool, str]:
        """Avalia a regra contra a topologia. Retorna (should_fire, reason)."""
        raise NotImplementedError


class SLOBurnRateAlert(ContextualRule):
    """Alerta baseado em SLO burn rate ao invés de threshold bruto."""

    def __init__(self, service: str, slo_target: float, burn_rate_threshold: float):
        super().__init__(
            id=f"CTX-SLO-{service}",
            name=f"SLO Burn Rate — {service}",
            description=f"Alerta quando o burn rate do SLO de {service} excede {burn_rate_threshold}x",
            conditions=[f"burn_rate > {burn_rate_threshold}x", f"SLO target: {slo_target:.2%}"],
            suppress_if=[f"dependency DOWN (causa raiz não é {service})"],
        )
        self.service = service
        self.slo_target = slo_target
        self.burn_rate_threshold = burn_rate_threshold

    def evaluate(self, topology: ServiceTopology) -> tuple[bool, str]:
        metrics = topology.metrics.get(self.service, {})
        error_rate = metrics.get("error_rate", 0)

        error_budget = 1 - self.slo_target
        burn_rate = error_rate / error_budget if error_budget > 0 else 0

        # Verificar supressão por dependência
        deps = topology.services.get(self.service, [])
        for dep in deps:
            if topology.states.get(dep) == ServiceState.DOWN:
                return False, f"SUPRIMIDO: dependência {dep} está DOWN (causa raiz provável)"

        # Verificar manutenção
        if topology.states.get(self.service) == ServiceState.MAINTENANCE:
            return False, f"SUPRIMIDO: {self.service} em manutenção programada"

        if burn_rate > self.burn_rate_threshold:
            return True, f"DISPARAR: burn_rate={burn_rate:.1f}x (threshold: {self.burn_rate_threshold}x)"

        return False, f"OK: burn_rate={burn_rate:.1f}x (abaixo do threshold)"


class CompositeHealthAlert(ContextualRule):
    """Alerta que considera a saúde composta do serviço + dependências."""

    def __init__(self, service: str, min_healthy_deps: int):
        deps_text = f"Alerta se menos de {min_healthy_deps} dependências estão saudáveis"
        super().__init__(
            id=f"CTX-HEALTH-{service}",
            name=f"Composite Health — {service}",
            description=deps_text,
            conditions=[deps_text],
            suppress_if=["Nenhuma — este é o alerta de mais alto nível"],
        )
        self.service = service
        self.min_healthy_deps = min_healthy_deps

    def evaluate(self, topology: ServiceTopology) -> tuple[bool, str]:
        deps = topology.services.get(self.service, [])
        healthy_deps = sum(
            1 for d in deps
            if topology.states.get(d) in (ServiceState.HEALTHY, None)
        )

        if healthy_deps < self.min_healthy_deps:
            unhealthy = [d for d in deps if topology.states.get(d) != ServiceState.HEALTHY]
            return True, f"DISPARAR: apenas {healthy_deps}/{len(deps)} deps saudáveis. DOWN: {unhealthy}"

        return False, f"OK: {healthy_deps}/{len(deps)} dependências saudáveis"


def build_scenario() -> ServiceTopology:
    """Cria cenário com database DOWN propagando falhas."""
    return ServiceTopology(
        services={
            "frontend":        ["api-gateway"],
            "api-gateway":     ["auth-service", "checkout-service", "product-service"],
            "auth-service":    ["database", "cache"],
            "checkout-service":["database", "payment-gateway"],
            "product-service": ["database", "cache"],
            "database":        [],
            "cache":           [],
            "payment-gateway": [],
        },
        states={
            "frontend":         ServiceState.DEGRADED,
            "api-gateway":      ServiceState.DEGRADED,
            "auth-service":     ServiceState.DOWN,
            "checkout-service": ServiceState.DOWN,
            "product-service":  ServiceState.DEGRADED,
            "database":         ServiceState.DOWN,
            "cache":            ServiceState.HEALTHY,
            "payment-gateway":  ServiceState.HEALTHY,
        },
        metrics={
            "frontend":         {"error_rate": 0.25, "latency_p99": 5000},
            "api-gateway":      {"error_rate": 0.30, "latency_p99": 8000},
            "auth-service":     {"error_rate": 0.95, "latency_p99": 30000},
            "checkout-service": {"error_rate": 0.88, "latency_p99": 25000},
            "product-service":  {"error_rate": 0.15, "latency_p99": 3000},
            "database":         {"error_rate": 1.00, "latency_p99": 0},
            "cache":            {"error_rate": 0.001, "latency_p99": 5},
            "payment-gateway":  {"error_rate": 0.002, "latency_p99": 200},
        },
    )


def run_demo() -> None:
    print("=" * 70)
    print("🎯 Demo: Alertas Contextuais e Investigação Operacional")
    print("   Curso 3 — Observabilidade Inteligente")
    print("=" * 70)

    topology = build_scenario()

    # Topologia
    print(f"\n{'─' * 70}")
    print("🗺️  TOPOLOGIA DO SISTEMA (estado atual)")
    print(f"{'─' * 70}")

    state_icons = {
        ServiceState.HEALTHY: "🟢", ServiceState.DEGRADED: "🟡",
        ServiceState.DOWN: "🔴", ServiceState.MAINTENANCE: "🔵",
    }

    for svc, deps in topology.services.items():
        state = topology.states[svc]
        deps_str = f" → [{', '.join(deps)}]" if deps else ""
        metrics = topology.metrics.get(svc, {})
        print(f"  {state_icons[state]} {svc:<20} {state.value:<12} "
              f"err={metrics.get('error_rate', 0):.0%}{deps_str}")

    # Alertas tradicionais (sem contexto)
    print(f"\n{'─' * 70}")
    print("📢 CENÁRIO A: Alertas TRADICIONAIS (sem contexto)")
    print(f"{'─' * 70}")

    traditional_count = 0
    threshold = 0.10
    for svc, metrics in topology.metrics.items():
        if metrics.get("error_rate", 0) > threshold:
            traditional_count += 1
            print(f"  🔔 [{svc}] error_rate={metrics['error_rate']:.0%} > {threshold:.0%}")

    print(f"\n  Total de alertas: {traditional_count}")
    print(f"  ⚠️  Time recebe {traditional_count} alertas SIMULTÂNEOS!")
    print(f"  ⚠️  Todos parecem críticos — qual investigar primeiro?")

    # Alertas contextuais (com topologia)
    print(f"\n{'─' * 70}")
    print("🎯 CENÁRIO B: Alertas CONTEXTUAIS (com dependências)")
    print(f"{'─' * 70}")

    rules = [
        SLOBurnRateAlert("auth-service", 0.999, 5.0),
        SLOBurnRateAlert("checkout-service", 0.999, 5.0),
        SLOBurnRateAlert("product-service", 0.999, 5.0),
        SLOBurnRateAlert("frontend", 0.995, 3.0),
        SLOBurnRateAlert("api-gateway", 0.999, 5.0),
        CompositeHealthAlert("api-gateway", 2),
    ]

    fired = []
    suppressed = []

    for rule in rules:
        should_fire, reason = rule.evaluate(topology)
        if should_fire:
            fired.append((rule, reason))
            print(f"  🔔 [{rule.id}] {rule.name}")
            print(f"     → {reason}")
        else:
            suppressed.append((rule, reason))
            print(f"  🔇 [{rule.id}] {rule.name}")
            print(f"     → {reason}")

    print(f"\n  Alertas disparados : {len(fired)}")
    print(f"  Alertas suprimidos : {len(suppressed)}")
    print(f"  Redução de ruído   : {len(suppressed)}/{len(rules)} ({len(suppressed) / len(rules) * 100:.0f}%)")

    # Comparativo
    print("\n" + "=" * 70)
    print("📊 COMPARATIVO")
    print("=" * 70)
    print(f"""
  {'Aspecto':<35} {'Tradicional':<20} {'Contextual':<20}
  {'─' * 35} {'─' * 20} {'─' * 20}
  {'Alertas disparados':<35} {traditional_count:<20} {len(fired):<20}
  {'Causa raiz identificada':<35} {'Não':<20} {'Sim (database)':<20}
  {'Alertas redundantes suprimidos':<35} {'0':<20} {f'{len(suppressed)}':<20}
  {'Tempo até foco na causa':<35} {'15-30 min':<20} {'< 2 min':<20}

  💡 O alerta contextual entende que auth-service e checkout-service
     estão DOWN PORQUE o database está DOWN — e suprime os alertas
     derivados, focando a atenção na CAUSA RAIZ.
    """)

    print("=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  Alertas contextuais transformam ruído em sinal ao considerar:
  1. DEPENDÊNCIAS: Se a causa raiz é um upstream, suprimir derivados
  2. SLOs: Alertar no impacto ao negócio, não em métricas brutas
  3. ESTADO: Considerar manutenção, deploys em progresso, etc.
  4. COMPOSIÇÃO: Combinar múltiplos sinais antes de alertar

  Na Aula 3.5 (Hands-on), vamos configurar tudo isso na prática.
    """)


if __name__ == "__main__":
    run_demo()
