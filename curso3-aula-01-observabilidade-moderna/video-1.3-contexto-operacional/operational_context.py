"""
Vídeo 1.3 — Observabilidade orientada por contexto operacional
==============================================================
Demonstra como metadados de contexto (deploys, configurações,
feature flags) correlacionados com telemetria permitem
identificar rapidamente a causa de degradações pós-release.

Conceitos demonstrados:
- Metadados de contexto em observabilidade
- Change correlation (correlação temporal de mudanças)
- Deploy markers e anotações em dashboards
- Detecção automática de regressões pós-deploy
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class ChangeType(str, Enum):
    DEPLOY = "DEPLOY"
    CONFIG_CHANGE = "CONFIG"
    FEATURE_FLAG = "FEATURE_FLAG"
    INFRA_CHANGE = "INFRA"
    DB_MIGRATION = "DB_MIGRATION"


class HealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"


@dataclass
class OperationalChange:
    """Representa uma alteração no ambiente operacional."""
    change_type: ChangeType
    service: str
    description: str
    timestamp: datetime
    author: str
    metadata: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return (
            f"  [{self.timestamp.strftime('%H:%M')}] "
            f"[{self.change_type.value:12}] "
            f"{self.service}: {self.description} (by {self.author})"
        )


@dataclass
class HealthSnapshot:
    """Snapshot da saúde de um serviço em um momento específico."""
    service: str
    status: HealthStatus
    error_rate: float
    latency_p99_ms: float
    timestamp: datetime
    slo_compliant: bool = True

    def __str__(self) -> str:
        icon = {"HEALTHY": "🟢", "DEGRADED": "🟡", "CRITICAL": "🔴"}[self.status.value]
        slo = "✅" if self.slo_compliant else "❌"
        return (
            f"  [{self.timestamp.strftime('%H:%M')}] {icon} {self.service:<20} "
            f"err={self.error_rate:.1%}  p99={self.latency_p99_ms:.0f}ms  SLO:{slo}"
        )


@dataclass
class ContextCorrelation:
    """Correlação entre uma mudança e seu impacto observado."""
    change: OperationalChange
    before: HealthSnapshot
    after: HealthSnapshot
    correlation_score: float  # 0.0 a 1.0
    likely_cause: bool

    def __str__(self) -> str:
        indicator = "🎯 PROVÁVEL CAUSA" if self.likely_cause else "   correlação baixa"
        return (
            f"  {indicator}\n"
            f"    Mudança  : {self.change.description}\n"
            f"    Horário  : {self.change.timestamp.strftime('%H:%M')}\n"
            f"    Antes    : err={self.before.error_rate:.1%} p99={self.before.latency_p99_ms:.0f}ms\n"
            f"    Depois   : err={self.after.error_rate:.1%} p99={self.after.latency_p99_ms:.0f}ms\n"
            f"    Score    : {self.correlation_score:.0%}\n"
        )


# ---------------------------------------------------------------------------
# Cenário: Múltiplas mudanças em uma manhã — qual causou a degradação?
# ---------------------------------------------------------------------------

def generate_scenario() -> tuple[list[OperationalChange], list[HealthSnapshot]]:
    """Gera um cenário com múltiplas mudanças operacionais e dados de saúde."""
    base = datetime(2024, 8, 12, 8, 0, 0)

    changes = [
        OperationalChange(
            change_type=ChangeType.CONFIG_CHANGE,
            service="api-gateway",
            description="Atualização de rate limiting: 1000→2000 req/s",
            timestamp=base + timedelta(minutes=15),
            author="platform-team",
            metadata={"config": "rate_limit", "old": 1000, "new": 2000},
        ),
        OperationalChange(
            change_type=ChangeType.DEPLOY,
            service="product-service",
            description="Deploy v3.1.0 — novo cache de catálogo",
            timestamp=base + timedelta(minutes=45),
            author="backend-team",
            metadata={"version": "v3.1.0", "commit": "f4e5d6c", "changes": 12},
        ),
        OperationalChange(
            change_type=ChangeType.FEATURE_FLAG,
            service="checkout-service",
            description="Feature flag 'new-payment-flow' ativada para 100%",
            timestamp=base + timedelta(hours=1, minutes=15),
            author="product-team",
            metadata={"flag": "new-payment-flow", "rollout": "100%"},
        ),
        OperationalChange(
            change_type=ChangeType.DB_MIGRATION,
            service="user-service",
            description="Migração: adição de índice em users.email",
            timestamp=base + timedelta(hours=1, minutes=30),
            author="dba-team",
            metadata={"migration": "add_index_users_email", "table": "users"},
        ),
        OperationalChange(
            change_type=ChangeType.DEPLOY,
            service="checkout-service",
            description="Deploy v2.8.0 — integração com novo gateway de pagamento",
            timestamp=base + timedelta(hours=2),
            author="payments-team",
            metadata={"version": "v2.8.0", "commit": "a1b2c3d", "changes": 28},
        ),
    ]

    # Snapshots de saúde ao longo do tempo
    snapshots = [
        # 08:00 — Baseline saudável
        HealthSnapshot("api-gateway",      HealthStatus.HEALTHY,  0.001, 45,   base),
        HealthSnapshot("product-service",  HealthStatus.HEALTHY,  0.002, 120,  base),
        HealthSnapshot("checkout-service", HealthStatus.HEALTHY,  0.003, 200,  base),
        HealthSnapshot("user-service",     HealthStatus.HEALTHY,  0.001, 80,   base),
        # 08:30 — Após config change (sem impacto)
        HealthSnapshot("api-gateway",      HealthStatus.HEALTHY,  0.001, 42,   base + timedelta(minutes=30)),
        HealthSnapshot("product-service",  HealthStatus.HEALTHY,  0.002, 118,  base + timedelta(minutes=30)),
        HealthSnapshot("checkout-service", HealthStatus.HEALTHY,  0.003, 195,  base + timedelta(minutes=30)),
        HealthSnapshot("user-service",     HealthStatus.HEALTHY,  0.001, 78,   base + timedelta(minutes=30)),
        # 09:00 — Após deploy product-service (sem impacto)
        HealthSnapshot("api-gateway",      HealthStatus.HEALTHY,  0.001, 44,   base + timedelta(hours=1)),
        HealthSnapshot("product-service",  HealthStatus.HEALTHY,  0.001, 85,   base + timedelta(hours=1)),
        HealthSnapshot("checkout-service", HealthStatus.HEALTHY,  0.003, 198,  base + timedelta(hours=1)),
        HealthSnapshot("user-service",     HealthStatus.HEALTHY,  0.001, 82,   base + timedelta(hours=1)),
        # 10:15 — 15min após deploy checkout v2.8.0 → DEGRADAÇÃO!
        HealthSnapshot("api-gateway",      HealthStatus.HEALTHY,  0.005, 180,  base + timedelta(hours=2, minutes=15)),
        HealthSnapshot("product-service",  HealthStatus.HEALTHY,  0.001, 88,   base + timedelta(hours=2, minutes=15)),
        HealthSnapshot("checkout-service", HealthStatus.DEGRADED, 0.12,  3200, base + timedelta(hours=2, minutes=15), slo_compliant=False),
        HealthSnapshot("user-service",     HealthStatus.HEALTHY,  0.002, 85,   base + timedelta(hours=2, minutes=15)),
        # 10:30 — Degradação piora
        HealthSnapshot("api-gateway",      HealthStatus.DEGRADED, 0.08,  850,  base + timedelta(hours=2, minutes=30)),
        HealthSnapshot("product-service",  HealthStatus.HEALTHY,  0.001, 90,   base + timedelta(hours=2, minutes=30)),
        HealthSnapshot("checkout-service", HealthStatus.CRITICAL, 0.35,  8500, base + timedelta(hours=2, minutes=30), slo_compliant=False),
        HealthSnapshot("user-service",     HealthStatus.HEALTHY,  0.002, 82,   base + timedelta(hours=2, minutes=30)),
    ]

    return changes, snapshots


def correlate_changes(
    changes: list[OperationalChange], snapshots: list[HealthSnapshot]
) -> list[ContextCorrelation]:
    """
    Correlaciona mudanças com impacto na saúde dos serviços.
    Usa proximidade temporal e serviço afetado como heurísticas.
    """
    correlations: list[ContextCorrelation] = []

    for change in changes:
        # Encontrar snapshot ANTES e DEPOIS da mudança para o serviço relevante
        service_snapshots = [s for s in snapshots if s.service == change.service]
        before = None
        after = None

        for snap in sorted(service_snapshots, key=lambda s: s.timestamp):
            if snap.timestamp <= change.timestamp:
                before = snap
            elif snap.timestamp > change.timestamp and after is None:
                after = snap

        if not before or not after:
            continue

        # Calcular score de correlação
        error_delta = after.error_rate - before.error_rate
        latency_delta = after.latency_p99_ms - before.latency_p99_ms
        time_proximity = (after.timestamp - change.timestamp).total_seconds() / 3600

        score = 0.0
        if error_delta > 0.05:
            score += 0.4
        if latency_delta > 500:
            score += 0.3
        if time_proximity < 0.5:
            score += 0.2
        if not after.slo_compliant and before.slo_compliant:
            score += 0.1

        correlations.append(ContextCorrelation(
            change=change,
            before=before,
            after=after,
            correlation_score=min(score, 1.0),
            likely_cause=score >= 0.6,
        ))

    return correlations


def run_demo() -> None:
    print("=" * 70)
    print("🔍 Demo: Observabilidade Orientada por Contexto Operacional")
    print("   Curso 3 — Observabilidade Inteligente")
    print("=" * 70)

    changes, snapshots = generate_scenario()

    # Timeline de mudanças
    print("\n" + "─" * 70)
    print("📋 TIMELINE DE MUDANÇAS OPERACIONAIS (manhã de 12/08/2024)")
    print("─" * 70)
    for c in changes:
        print(c)

    # Evolução da saúde
    print("\n" + "─" * 70)
    print("📊 EVOLUÇÃO DA SAÚDE DOS SERVIÇOS")
    print("─" * 70)

    time_groups: dict[str, list[HealthSnapshot]] = {}
    for snap in snapshots:
        key = snap.timestamp.strftime('%H:%M')
        time_groups.setdefault(key, []).append(snap)

    for time_key in sorted(time_groups.keys()):
        print(f"\n  ⏰ {time_key}:")
        for snap in time_groups[time_key]:
            print(f"  {snap}")

    # Correlação automática
    print("\n" + "─" * 70)
    print("🔗 CORRELAÇÃO AUTOMÁTICA: MUDANÇAS × IMPACTO")
    print("─" * 70)

    correlations = correlate_changes(changes, snapshots)
    correlations.sort(key=lambda c: c.correlation_score, reverse=True)

    for corr in correlations:
        print(corr)

    # Diagnóstico
    likely = [c for c in correlations if c.likely_cause]
    if likely:
        cause = likely[0]
        print("=" * 70)
        print("🎯 DIAGNÓSTICO CONTEXTUAL")
        print("=" * 70)
        print(f"""
  Causa mais provável: {cause.change.description}
  Tipo de mudança    : {cause.change.change_type.value}
  Autor              : {cause.change.author}
  Horário da mudança : {cause.change.timestamp.strftime('%H:%M')}
  Score de correlação: {cause.correlation_score:.0%}

  Impacto observado:
    Error rate : {cause.before.error_rate:.1%} → {cause.after.error_rate:.1%}
    Latência   : {cause.before.latency_p99_ms:.0f}ms → {cause.after.latency_p99_ms:.0f}ms
    SLO        : {'Cumprido' if cause.before.slo_compliant else 'Violado'} → {'Cumprido' if cause.after.slo_compliant else 'Violado'}

  ✅ AÇÃO RECOMENDADA:
    1. Rollback {cause.change.service} para a versão anterior
    2. Investigar o commit {cause.change.metadata.get('commit', 'N/A')}
    3. Adicionar testes de integração para o novo gateway de pagamento
        """)

    print("=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  Sem metadados de contexto, a equipe investigaria TODOS os serviços.
  Com contexto operacional, a correlação automática aponta diretamente
  para a mudança mais provável, reduzindo o MTTR significativamente.

  Na Aula 1.4, veremos como o OpenTelemetry padroniza a coleta
  desses metadados de forma agnóstica de ferramentas.
    """)


if __name__ == "__main__":
    run_demo()
