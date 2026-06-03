"""
Vídeo 1.2 — Correlacionando incidentes automaticamente
=======================================================
Motor simplificado de correlação de eventos multimodal.
Demonstra como plataformas de AIOps agrupam logs, métricas
e traces relacionados a uma mesma falha usando:

  1. Correlação temporal (time-window)
  2. Correlação topológica (dependências de serviço)
  3. Correlação por trace_id (distributed tracing)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum


# ---------------------------------------------------------------------------
# Modelos de dados — os 3 pilares da observabilidade
# ---------------------------------------------------------------------------

class SignalType(str, Enum):
    LOG    = "LOG"
    METRIC = "METRIC"
    TRACE  = "TRACE"


@dataclass
class Signal:
    """Representa um sinal de observabilidade (log, métrica ou trace)."""
    signal_type: SignalType
    service: str
    timestamp: datetime
    message: str
    trace_id: Optional[str] = None
    value: Optional[float] = None  # para métricas
    tags: dict = field(default_factory=dict)


@dataclass
class CorrelatedIncident:
    """Agrupa sinais correlacionados em um único incidente."""
    incident_id: str
    root_service: str
    signals: list[Signal] = field(default_factory=list)
    confidence: float = 0.0  # 0-1: confiança na correlação

    @property
    def signal_count(self) -> int:
        return len(self.signals)

    @property
    def affected_services(self) -> set[str]:
        return {s.service for s in self.signals}

    @property
    def signal_types(self) -> set[SignalType]:
        return {s.signal_type for s in self.signals}


# ---------------------------------------------------------------------------
# Motor de correlação
# ---------------------------------------------------------------------------

SERVICE_DEPS: dict[str, list[str]] = {
    "database":        [],
    "cache":           ["database"],
    "auth-service":    ["database", "cache"],
    "api-gateway":     ["auth-service"],
    "frontend":        ["api-gateway"],
}


def get_upstream_services(service: str) -> set[str]:
    """Retorna todos os serviços upstream (dependências transitivas)."""
    visited = set()
    queue = [service]
    while queue:
        svc = queue.pop()
        for dep in SERVICE_DEPS.get(svc, []):
            if dep not in visited:
                visited.add(dep)
                queue.append(dep)
    return visited


class EventCorrelator:
    """
    Motor de correlação de eventos que agrupa sinais usando três estratégias:
    1. Temporal: sinais dentro de uma janela de tempo
    2. Topológica: serviços que dependem uns dos outros
    3. Trace-based: mesmo trace_id em distributed tracing
    """

    def __init__(self, time_window_seconds: int = 120):
        self.time_window = timedelta(seconds=time_window_seconds)
        self._signals: list[Signal] = []
        self._incidents: list[CorrelatedIncident] = []

    def ingest(self, signal: Signal) -> None:
        """Ingere um novo sinal e tenta correlacioná-lo."""
        self._signals.append(signal)
        self._correlate(signal)

    def _correlate(self, new_signal: Signal) -> None:
        """Tenta correlacionar o novo sinal com incidentes existentes."""

        # 1. Correlação por trace_id
        if new_signal.trace_id:
            for incident in self._incidents:
                if any(s.trace_id == new_signal.trace_id for s in incident.signals):
                    incident.signals.append(new_signal)
                    incident.confidence = min(1.0, incident.confidence + 0.15)
                    return

        # 2. Correlação topológica + temporal
        for incident in self._incidents:
            time_diff = abs((new_signal.timestamp - incident.signals[0].timestamp).total_seconds())
            if time_diff > self.time_window.total_seconds():
                continue  # fora da janela

            # verifica se o serviço está relacionado topologicamente
            upstream = get_upstream_services(new_signal.service)
            known_services = incident.affected_services
            if new_signal.service in known_services or upstream & known_services:
                incident.signals.append(new_signal)
                incident.confidence = min(1.0, incident.confidence + 0.10)
                return

        # 3. Nenhuma correlação — cria novo incidente
        inc_id = f"INC-{len(self._incidents) + 1:04d}"
        new_incident = CorrelatedIncident(
            incident_id=inc_id,
            root_service=new_signal.service,
            signals=[new_signal],
            confidence=0.5,
        )
        self._incidents.append(new_incident)

    def get_incidents(self) -> list[CorrelatedIncident]:
        return sorted(self._incidents, key=lambda i: i.signal_count, reverse=True)

    def report(self) -> None:
        """Exibe relatório de correlação."""
        print("\n" + "=" * 65)
        print("📋 RELATÓRIO DE CORRELAÇÃO DE EVENTOS")
        print("=" * 65)

        total_signals = len(self._signals)
        incidents = self.get_incidents()
        print(f"\n  Sinais ingeridos : {total_signals}")
        print(f"  Incidentes únicos: {len(incidents)}")
        reduction = (1 - len(incidents) / total_signals) * 100 if total_signals > 0 else 0
        print(f"  Redução de ruído : {reduction:.0f}%\n")

        for inc in incidents:
            types = ", ".join(t.value for t in inc.signal_types)
            print(f"  {'─'*55}")
            print(f"  🔴 {inc.incident_id} | Serviço raiz: {inc.root_service}")
            print(f"     Sinais agrupados : {inc.signal_count}")
            print(f"     Serviços afetados: {', '.join(inc.affected_services)}")
            print(f"     Tipos de sinal   : {types}")
            print(f"     Confiança        : {inc.confidence:.0%}")


# ---------------------------------------------------------------------------
# Demonstração
# ---------------------------------------------------------------------------

def build_demo_signals() -> list[Signal]:
    """Gera sinais simulados de uma falha de banco de dados."""
    base_time = datetime.now()

    return [
        # --- Logs ---
        Signal(SignalType.LOG, "database", base_time,
               "Connection pool exhausted: too many connections", trace_id="trace-abc"),
        Signal(SignalType.LOG, "cache", base_time + timedelta(seconds=5),
               "Cache backend unavailable, fallback to DB failed"),
        Signal(SignalType.LOG, "auth-service", base_time + timedelta(seconds=10),
               "Auth token validation failed: DB unreachable", trace_id="trace-abc"),
        Signal(SignalType.LOG, "api-gateway", base_time + timedelta(seconds=15),
               "Upstream auth-service timeout"),
        Signal(SignalType.LOG, "frontend", base_time + timedelta(seconds=20),
               "503 Service Unavailable returned to user"),

        # --- Métricas ---
        Signal(SignalType.METRIC, "database", base_time + timedelta(seconds=2),
               "connections_active", value=498.0, tags={"threshold": "500"}),
        Signal(SignalType.METRIC, "auth-service", base_time + timedelta(seconds=12),
               "request_error_rate", value=0.98, tags={"threshold": "0.05"}),
        Signal(SignalType.METRIC, "api-gateway", base_time + timedelta(seconds=17),
               "latency_p99_ms", value=9800.0, tags={"threshold": "500"}),

        # --- Traces ---
        Signal(SignalType.TRACE, "auth-service", base_time + timedelta(seconds=8),
               "Span auth.validate FAILED", trace_id="trace-abc"),
        Signal(SignalType.TRACE, "api-gateway", base_time + timedelta(seconds=13),
               "Span gateway.route FAILED", trace_id="trace-abc"),

        # --- Sinal não relacionado (ruído) ---
        Signal(SignalType.LOG, "payment-service", base_time + timedelta(minutes=10),
               "Scheduled job completed: invoice generation"),  # evento isolado, sem relação
    ]


if __name__ == "__main__":
    print("🔬 Demo: Correlação Automática de Eventos Multimodal")
    print("     Nível 1 — AIOps & Automação de Incidentes\n")

    correlator = EventCorrelator(time_window_seconds=120)
    signals = build_demo_signals()

    print("📥 Ingerindo sinais em tempo real...\n")
    for signal in signals:
        print(f"  → [{signal.signal_type.value}] {signal.service}: {signal.message[:60]}")
        correlator.ingest(signal)

    correlator.report()

    print("\n" + "=" * 65)
    print("📌 CONCLUSÃO")
    print("=" * 65)
    print("""
  Ao correlacionar temporal e topologicamente os sinais,
  reduzimos de 11 alertas individuais para apenas 2 incidentes
  distintos — um real e um evento isolado sem impacto.

  Plataformas como Datadog, Dynatrace e New Relic fazem isso
  automaticamente usando ML e a topologia do seu ambiente.
    """)
