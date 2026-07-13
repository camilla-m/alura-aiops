"""
Vídeo 5.1 — Centralizando sinais operacionais em ambientes modernos
=====================================================================
Demonstra arquitetura de unificação de CI/CD, deploys, logs e traces
em um único hub centralizado de sinais operacionais.

Conceitos demonstrados:
- Hub de sinais: ponto único de correlação
- Ingestão de múltiplas fontes (CI/CD, APM, infra, logs)
- Metadados compartilhados (resource attributes)
- Visão unificada para investigação
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class SignalSource(str, Enum):
    CICD = "CI/CD"
    APM = "APM"
    INFRA = "INFRA"
    LOGS = "LOGS"
    ALERTS = "ALERTS"
    INCIDENTS = "INCIDENTS"


@dataclass
class UnifiedSignal:
    source: SignalSource
    service: str
    event_type: str
    message: str
    timestamp: datetime
    metadata: dict = field(default_factory=dict)
    correlation_id: str = ""

    def __str__(self) -> str:
        src = f"[{self.source.value:10}]"
        corr = f" (corr:{self.correlation_id[:8]})" if self.correlation_id else ""
        return f"  {src} [{self.timestamp.strftime('%H:%M:%S')}] {self.service}: {self.message}{corr}"


@dataclass
class SignalHub:
    """Hub centralizado que recebe e correlaciona sinais de múltiplas fontes."""
    signals: list[UnifiedSignal] = field(default_factory=list)

    def ingest(self, signal: UnifiedSignal) -> None:
        self.signals.append(signal)

    def get_timeline(self, service: str | None = None) -> list[UnifiedSignal]:
        filtered = self.signals if service is None else [s for s in self.signals if s.service == service]
        return sorted(filtered, key=lambda s: s.timestamp)

    def get_by_correlation(self, corr_id: str) -> list[UnifiedSignal]:
        return sorted(
            [s for s in self.signals if s.correlation_id == corr_id],
            key=lambda s: s.timestamp,
        )

    def get_by_source(self, source: SignalSource) -> list[UnifiedSignal]:
        return [s for s in self.signals if s.source == source]


def build_scenario() -> SignalHub:
    """Cria cenário com sinais de múltiplas fontes correlacionados."""
    hub = SignalHub()
    base = datetime(2024, 9, 2, 10, 0, 0)
    corr_id = "deploy-checkout-v6"

    signals = [
        # CI/CD pipeline
        UnifiedSignal(SignalSource.CICD, "checkout-service", "pipeline.start",
            "Pipeline #4521 started (branch: main, commit: e4f5g6h)",
            base - timedelta(minutes=30), {"pipeline_id": "4521", "branch": "main"}, corr_id),
        UnifiedSignal(SignalSource.CICD, "checkout-service", "test.pass",
            "All 342 tests passed (unit: 298, integration: 44)",
            base - timedelta(minutes=20), {"tests_total": 342}, corr_id),
        UnifiedSignal(SignalSource.CICD, "checkout-service", "build.success",
            "Docker image built: checkout-service:v6.0.0-sha-e4f5g6h",
            base - timedelta(minutes=15), {"image_tag": "v6.0.0"}, corr_id),
        UnifiedSignal(SignalSource.CICD, "checkout-service", "deploy.canary",
            "Canary deployment started (10% traffic)",
            base - timedelta(minutes=10), {"canary_pct": 10}, corr_id),
        UnifiedSignal(SignalSource.CICD, "checkout-service", "deploy.promote",
            "Canary promoted to 100% — deployment complete",
            base, {"canary_pct": 100}, corr_id),

        # APM signals
        UnifiedSignal(SignalSource.APM, "checkout-service", "latency.change",
            "p99 latency shifted: 180ms → 320ms (+78%)",
            base + timedelta(minutes=5), {"p99_before": 180, "p99_after": 320}, corr_id),
        UnifiedSignal(SignalSource.APM, "checkout-service", "error_rate.spike",
            "Error rate increased: 0.1% → 2.3%",
            base + timedelta(minutes=8), {"error_rate": 0.023}, corr_id),
        UnifiedSignal(SignalSource.APM, "payment-service", "upstream.degraded",
            "Upstream checkout-service showing elevated latency",
            base + timedelta(minutes=10), {"upstream": "checkout-service"}, corr_id),

        # Infrastructure
        UnifiedSignal(SignalSource.INFRA, "checkout-service", "cpu.spike",
            "CPU utilization: 45% → 82% on pods checkout-*",
            base + timedelta(minutes=6), {"cpu_pct": 82}),
        UnifiedSignal(SignalSource.INFRA, "checkout-service", "memory.increase",
            "Memory RSS: 512MB → 890MB (+74%)",
            base + timedelta(minutes=7), {"memory_mb": 890}),

        # Logs
        UnifiedSignal(SignalSource.LOGS, "checkout-service", "error",
            "ERROR: Serialization failed — new field 'discount_code' not in schema",
            base + timedelta(minutes=5, seconds=30), {"error_type": "SerializationError"}, corr_id),
        UnifiedSignal(SignalSource.LOGS, "checkout-service", "error",
            "ERROR: Retry exhausted for Redis write (3/3 attempts)",
            base + timedelta(minutes=9), {"retries": 3}, corr_id),

        # Alert
        UnifiedSignal(SignalSource.ALERTS, "checkout-service", "slo.breach",
            "SLO breach: error_rate > 1% for 5 minutes (current: 2.3%)",
            base + timedelta(minutes=12), {"slo": "error_rate", "threshold": 0.01}, corr_id),

        # Incident
        UnifiedSignal(SignalSource.INCIDENTS, "checkout-service", "incident.created",
            "INC-2024-0902: Checkout degradation post-deploy v6.0.0",
            base + timedelta(minutes=13), {"incident_id": "INC-2024-0902"}, corr_id),
    ]

    for s in signals:
        hub.ingest(s)

    return hub


def run_demo() -> None:
    print("=" * 70)
    print("🔗 Demo: Hub Centralizado de Sinais Operacionais")
    print("   Curso 3 — Observabilidade Inteligente")
    print("=" * 70)

    hub = build_scenario()

    # Visão por fonte (silos)
    print(f"\n{'─' * 70}")
    print("📊 VISÃO ISOLADA (cada time vê apenas seus sinais)")
    print(f"{'─' * 70}")

    for source in SignalSource:
        signals = hub.get_by_source(source)
        if signals:
            print(f"\n  📦 {source.value} ({len(signals)} sinais):")
            for s in signals:
                print(f"    [{s.timestamp.strftime('%H:%M')}] {s.message[:60]}")

    print(f"\n  ⚠️  Cada time vê uma fração do problema!")
    print(f"     CI/CD sabe do deploy, mas não vê os erros de runtime")
    print(f"     APM vê latência, mas não sabe da causa (deploy)")
    print(f"     Infra vê CPU/memória, mas não sabe do contexto")

    # Visão unificada (hub)
    print(f"\n{'─' * 70}")
    print("🔗 VISÃO UNIFICADA (hub de sinais)")
    print(f"{'─' * 70}")

    timeline = hub.get_timeline()
    print(f"\n  Timeline completa ({len(timeline)} sinais):\n")
    for s in timeline:
        print(s)

    # Correlação
    print(f"\n{'─' * 70}")
    print("🎯 CORRELAÇÃO AUTOMÁTICA (por correlation_id)")
    print(f"{'─' * 70}")

    correlated = hub.get_by_correlation("deploy-checkout-v6")
    print(f"\n  {len(correlated)} sinais correlacionados ao deploy:\n")
    for s in correlated:
        print(s)

    print(f"""
  💡 A correlação automática revela:
  1. Deploy v6.0.0 às 10:00 (CI/CD)
  2. Latência sobe +78% em 5 min (APM)
  3. Novo campo 'discount_code' causa SerializationError (LOGS)
  4. CPU e memória sobem por retries (INFRA)
  5. SLO breach dispara alerta (ALERTS)
  6. Incidente criado automaticamente (INCIDENTS)

  → Toda a cadeia visível em UMA timeline unificada
    """)

    print("=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  O hub de sinais unifica dados de CI/CD, APM, infra, logs e alertas
  em uma timeline correlacionada. Isso elimina o "alt-tab entre
  10 ferramentas" e permite diagnóstico em minutos.

  Na Aula 5.2, veremos como traduzir esses sinais técnicos em
  impacto de negócios para a gestão sênior.
    """)


if __name__ == "__main__":
    run_demo()
