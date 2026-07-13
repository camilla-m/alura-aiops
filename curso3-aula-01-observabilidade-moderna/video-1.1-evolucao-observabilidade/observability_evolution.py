"""
Vídeo 1.1 — A evolução da observabilidade em ambientes modernos
================================================================
Demonstra a diferença entre monitoramento black-box tradicional
e observabilidade distribuída moderna com dados correlacionados.

Conceitos demonstrados:
- Monitoramento black-box vs. observabilidade distribuída
- Limitações de verificações externas (ping, HTTP status)
- O poder dos dados correlacionados com contexto
- Visibilidade interna vs. externa em arquiteturas complexas
"""

import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class MonitoringApproach(str, Enum):
    BLACKBOX = "BLACK-BOX"
    OBSERVABILITY = "OBSERVABILIDADE"


class ServiceStatus(str, Enum):
    HEALTHY = "✅ HEALTHY"
    DEGRADED = "⚠️ DEGRADED"
    DOWN = "❌ DOWN"
    UNKNOWN = "❓ UNKNOWN"


@dataclass
class BlackBoxCheck:
    """Verificação externa simples — o que o monitoramento antigo vê."""
    service: str
    endpoint: str
    status_code: int
    response_time_ms: float
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def status(self) -> ServiceStatus:
        if self.status_code >= 500:
            return ServiceStatus.DOWN
        if self.response_time_ms > 5000:
            return ServiceStatus.DEGRADED
        return ServiceStatus.HEALTHY

    def __str__(self) -> str:
        return (
            f"  [{self.timestamp.strftime('%H:%M:%S')}] "
            f"GET {self.endpoint} → {self.status_code} "
            f"({self.response_time_ms:.0f}ms) {self.status.value}"
        )


@dataclass
class ObservabilitySignal:
    """Sinal rico de observabilidade — o que a instrumentação moderna expõe."""
    service: str
    signal_type: str  # METRIC, LOG, TRACE
    message: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        trace = f" [trace:{self.trace_id[:8]}]" if self.trace_id else ""
        meta = f" {self.metadata}" if self.metadata else ""
        return (
            f"  [{self.timestamp.strftime('%H:%M:%S')}] "
            f"[{self.signal_type}] {self.service}: "
            f"{self.message}{trace}{meta}"
        )


# ---------------------------------------------------------------------------
# Cenário: Deploy com bug sutil causa degradação em cascata
# ---------------------------------------------------------------------------

SERVICES = [
    "api-gateway", "user-service", "product-service",
    "cart-service", "payment-service", "database",
]


def simulate_blackbox_monitoring() -> list[BlackBoxCheck]:
    """
    Simula o que o monitoramento black-box enxerga:
    apenas status codes e tempos de resposta.
    """
    checks: list[BlackBoxCheck] = []
    base_time = datetime(2024, 7, 15, 14, 30, 0)

    # Antes do incidente — tudo parece saudável
    for i, svc in enumerate(SERVICES):
        checks.append(BlackBoxCheck(
            service=svc,
            endpoint=f"/{svc}/health",
            status_code=200,
            response_time_ms=random.uniform(50, 200),
            timestamp=base_time + timedelta(seconds=i * 2),
        ))

    # Durante o incidente — só vê sintomas externos
    incident_time = base_time + timedelta(minutes=5)
    incident_responses = {
        "api-gateway":      (504, 30000),
        "user-service":     (200, 180),    # Parece saudável!
        "product-service":  (200, 150),    # Parece saudável!
        "cart-service":     (503, 15000),
        "payment-service":  (500, 28000),
        "database":         (200, 90),     # Health check passa!
    }

    for i, (svc, (code, latency)) in enumerate(incident_responses.items()):
        checks.append(BlackBoxCheck(
            service=svc,
            endpoint=f"/{svc}/health",
            status_code=code,
            response_time_ms=latency + random.uniform(-20, 20),
            timestamp=incident_time + timedelta(seconds=i * 3),
        ))

    return checks


def simulate_observability_signals() -> list[ObservabilitySignal]:
    """
    Simula os sinais ricos que a observabilidade distribuída expõe:
    métricas internas, logs estruturados e traces correlacionados.
    """
    signals: list[ObservabilitySignal] = []
    base_time = datetime(2024, 7, 15, 14, 35, 0)
    trace_id = "abc123def456789012345678"

    # Deploy detectado como evento contextual
    signals.append(ObservabilitySignal(
        service="deploy-controller",
        signal_type="EVENT",
        message="Deploy user-service v2.4.1 → v2.4.2 iniciado",
        metadata={"version": "v2.4.2", "commit": "a1b2c3d", "author": "dev-team"},
        timestamp=base_time - timedelta(minutes=2),
    ))

    # Sinais internos revelam a verdadeira causa
    signals.extend([
        ObservabilitySignal(
            service="user-service",
            signal_type="LOG",
            message="WARN: Connection pool utilization at 95% (new query pattern from v2.4.2)",
            trace_id=trace_id,
            metadata={"pool_active": 95, "pool_max": 100, "version": "v2.4.2"},
            timestamp=base_time,
        ),
        ObservabilitySignal(
            service="database",
            signal_type="METRIC",
            message="active_connections=97/100, slow_queries=42/min",
            metadata={"slow_query_pattern": "SELECT * FROM users WHERE ... (missing index)"},
            timestamp=base_time + timedelta(seconds=5),
        ),
        ObservabilitySignal(
            service="user-service",
            signal_type="TRACE",
            message="GET /api/users/:id → 200 (8200ms) — db_query took 7800ms",
            trace_id=trace_id,
            span_id="span-user-001",
            metadata={"db_query_ms": 7800, "total_ms": 8200},
            timestamp=base_time + timedelta(seconds=8),
        ),
        ObservabilitySignal(
            service="cart-service",
            signal_type="TRACE",
            message="POST /api/cart/checkout → timeout waiting for user-service",
            trace_id=trace_id,
            span_id="span-cart-001",
            metadata={"upstream": "user-service", "timeout_ms": 15000},
            timestamp=base_time + timedelta(seconds=15),
        ),
        ObservabilitySignal(
            service="payment-service",
            signal_type="LOG",
            message="ERROR: Payment flow aborted — dependency user-service unhealthy",
            trace_id=trace_id,
            metadata={"circuit_breaker": "OPEN", "dependency": "user-service"},
            timestamp=base_time + timedelta(seconds=20),
        ),
        ObservabilitySignal(
            service="api-gateway",
            signal_type="METRIC",
            message="error_rate=0.68, p99_latency=28000ms (SLO breach: p99 < 500ms)",
            metadata={"slo_status": "BREACHED", "error_budget_remaining": "-12%"},
            timestamp=base_time + timedelta(seconds=25),
        ),
    ])

    return signals


def run_comparison() -> None:
    """Executa e compara as duas abordagens lado a lado."""
    print("=" * 70)
    print("🔍 Comparativo: Monitoramento Black-Box vs. Observabilidade Moderna")
    print("   Curso 3 — Observabilidade Inteligente")
    print("=" * 70)

    # --- BLACK-BOX ---
    print("\n" + "─" * 70)
    print(f"📡 ABORDAGEM 1: MONITORAMENTO BLACK-BOX (externo)")
    print("─" * 70)
    print("  O que o time de operações vê com verificações HTTP externas:\n")

    bb_checks = simulate_blackbox_monitoring()

    print("  ANTES do incidente:")
    for c in bb_checks[:len(SERVICES)]:
        print(c)

    print(f"\n  ⏰ 5 minutos depois...\n")
    print("  DURANTE o incidente:")
    for c in bb_checks[len(SERVICES):]:
        print(c)

    # Diagnóstico black-box
    failing = [c for c in bb_checks[len(SERVICES):] if c.status != ServiceStatus.HEALTHY]
    print(f"\n  ❓ DIAGNÓSTICO BLACK-BOX:")
    print(f"     Serviços com problema: {', '.join(c.service for c in failing)}")
    print(f"     Causa raiz: DESCONHECIDA")
    print(f"     O database parece saudável (health check = 200)")
    print(f"     user-service e product-service parecem saudáveis")
    print(f"     → Time precisa investigar MANUALMENTE cada serviço")

    # --- OBSERVABILIDADE ---
    print("\n" + "─" * 70)
    print(f"🔭 ABORDAGEM 2: OBSERVABILIDADE DISTRIBUÍDA (instrumentação interna)")
    print("─" * 70)
    print("  O que os sinais correlacionados revelam:\n")

    obs_signals = simulate_observability_signals()
    for s in obs_signals:
        print(s)

    print(f"\n  🎯 DIAGNÓSTICO COM OBSERVABILIDADE:")
    print(f"     Causa raiz: Deploy user-service v2.4.2 introduziu query sem índice")
    print(f"     Cadeia:     Deploy → slow queries → connection pool saturado → cascata")
    print(f"     Trace ID:   {obs_signals[1].trace_id[:8]}... (correlaciona 4 serviços)")
    print(f"     Ação:       Rollback para v2.4.1 + adicionar índice no próximo deploy")
    print(f"     Tempo:      ~2 min para diagnóstico (vs. 30+ min com black-box)")

    # --- RESUMO ---
    print("\n" + "=" * 70)
    print("📊 RESUMO COMPARATIVO")
    print("=" * 70)

    comparison = [
        ("Visibilidade",         "Status codes externos",     "Estado interno de cada componente"),
        ("Correlação",           "Nenhuma — alertas isolados", "Traces ligam todo o fluxo"),
        ("Contexto de mudanças", "Não existe",                 "Deploy detectado automaticamente"),
        ("Causa raiz",           "Investigação manual",        "Identificada em ~2 minutos"),
        ("MTTR estimado",        "30-90 minutos",              "5-15 minutos"),
    ]

    print(f"\n  {'Aspecto':<25} {'Black-Box':<32} {'Observabilidade':<35}")
    print(f"  {'─'*25} {'─'*32} {'─'*35}")
    for aspect, bb, obs in comparison:
        print(f"  {aspect:<25} {bb:<32} {obs:<35}")

    print("\n" + "=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  O monitoramento black-box responde apenas "o serviço está UP ou DOWN?"
  A observabilidade moderna responde "POR QUE o serviço está se comportando assim?"

  Na Aula 1.2, vamos explorar como correlacionar métricas, logs e traces
  de forma integrada para acelerar ainda mais o troubleshooting.
    """)


if __name__ == "__main__":
    run_comparison()
