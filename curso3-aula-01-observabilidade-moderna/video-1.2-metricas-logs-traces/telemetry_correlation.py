"""
Vídeo 1.2 — Métricas, logs e traces no troubleshooting moderno
===============================================================
Demonstra como correlacionar as três verticais clássicas da telemetria
(métricas, logs e traces) de forma integrada para localizar falhas
sem saltar entre ferramentas isoladas.

Conceitos demonstrados:
- Navegação integrada de logs a traces
- Correlação por trace_id e span_id
- Enriquecimento de sinais com metadados comuns
- Redução do tempo de troubleshooting
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class SignalType(str, Enum):
    METRIC = "METRIC"
    LOG    = "LOG"
    TRACE  = "TRACE"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO  = "INFO"
    WARN  = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"


@dataclass
class TelemetrySignal:
    """Sinal unificado de telemetria com metadados de correlação."""
    signal_type: SignalType
    service: str
    message: str
    timestamp: datetime
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    level: Optional[LogLevel] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    labels: dict = field(default_factory=dict)

    def __str__(self) -> str:
        parts = [
            f"[{self.timestamp.strftime('%H:%M:%S.%f')[:12]}]",
            f"[{self.signal_type.value:6}]",
        ]
        if self.level:
            parts.append(f"[{self.level.value:5}]")
        parts.append(f"{self.service}:")
        parts.append(self.message)
        if self.trace_id:
            parts.append(f"(trace:{self.trace_id[:8]})")
        return " ".join(parts)


@dataclass
class TraceSpan:
    """Um span dentro de um trace distribuído."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    service: str
    operation: str
    duration_ms: float
    status_code: int
    start_time: datetime
    attributes: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Cenário: Requisição lenta de checkout — rastreando de ponta a ponta
# ---------------------------------------------------------------------------

def generate_trace_scenario() -> tuple[str, list[TraceSpan], list[TelemetrySignal]]:
    """
    Gera um cenário completo de trace com spans correlacionados,
    logs e métricas associados ao mesmo trace_id.
    """
    trace_id = uuid.uuid4().hex[:24]
    base_time = datetime(2024, 7, 15, 10, 30, 0)

    # Span IDs
    gw_span   = uuid.uuid4().hex[:16]
    cart_span  = uuid.uuid4().hex[:16]
    user_span  = uuid.uuid4().hex[:16]
    db_span    = uuid.uuid4().hex[:16]
    pay_span   = uuid.uuid4().hex[:16]

    spans = [
        TraceSpan(
            trace_id=trace_id, span_id=gw_span, parent_span_id=None,
            service="api-gateway", operation="POST /checkout",
            duration_ms=8500, status_code=504,
            start_time=base_time,
            attributes={"http.method": "POST", "http.target": "/checkout"},
        ),
        TraceSpan(
            trace_id=trace_id, span_id=cart_span, parent_span_id=gw_span,
            service="cart-service", operation="processCheckout",
            duration_ms=8200, status_code=500,
            start_time=base_time + timedelta(milliseconds=50),
            attributes={"cart.items": 3, "cart.total": 299.90},
        ),
        TraceSpan(
            trace_id=trace_id, span_id=user_span, parent_span_id=cart_span,
            service="user-service", operation="getUserProfile",
            duration_ms=7800, status_code=200,
            start_time=base_time + timedelta(milliseconds=100),
            attributes={"user.id": "usr-42", "cache.hit": False},
        ),
        TraceSpan(
            trace_id=trace_id, span_id=db_span, parent_span_id=user_span,
            service="database", operation="SELECT users WHERE id=?",
            duration_ms=7500, status_code=200,
            start_time=base_time + timedelta(milliseconds=150),
            attributes={"db.type": "postgresql", "db.statement": "SELECT * FROM users WHERE id=$1"},
        ),
        TraceSpan(
            trace_id=trace_id, span_id=pay_span, parent_span_id=cart_span,
            service="payment-service", operation="processPayment",
            duration_ms=0, status_code=503,
            start_time=base_time + timedelta(milliseconds=8300),
            attributes={"error": "upstream_timeout", "dependency": "cart-service"},
        ),
    ]

    # Sinais correlacionados ao mesmo trace
    signals: list[TelemetrySignal] = [
        # Logs
        TelemetrySignal(
            signal_type=SignalType.LOG, service="api-gateway",
            message="Incoming request POST /checkout from client 192.168.1.42",
            timestamp=base_time, trace_id=trace_id, span_id=gw_span,
            level=LogLevel.INFO,
        ),
        TelemetrySignal(
            signal_type=SignalType.LOG, service="cart-service",
            message="Processing checkout for cart_id=cart-789 (3 items, R$299.90)",
            timestamp=base_time + timedelta(milliseconds=55),
            trace_id=trace_id, span_id=cart_span, level=LogLevel.INFO,
        ),
        TelemetrySignal(
            signal_type=SignalType.LOG, service="user-service",
            message="Cache MISS for user usr-42 — falling back to database",
            timestamp=base_time + timedelta(milliseconds=110),
            trace_id=trace_id, span_id=user_span, level=LogLevel.WARN,
        ),
        TelemetrySignal(
            signal_type=SignalType.LOG, service="database",
            message="SLOW QUERY: SELECT * FROM users WHERE id=$1 — 7500ms (threshold: 100ms)",
            timestamp=base_time + timedelta(milliseconds=7650),
            trace_id=trace_id, span_id=db_span, level=LogLevel.ERROR,
        ),
        TelemetrySignal(
            signal_type=SignalType.LOG, service="cart-service",
            message="ERROR: Checkout timeout — user-service took 7800ms (max: 5000ms)",
            timestamp=base_time + timedelta(milliseconds=8200),
            trace_id=trace_id, span_id=cart_span, level=LogLevel.ERROR,
        ),
        TelemetrySignal(
            signal_type=SignalType.LOG, service="payment-service",
            message="ERROR: Cannot process payment — cart-service returned 500",
            timestamp=base_time + timedelta(milliseconds=8350),
            trace_id=trace_id, span_id=pay_span, level=LogLevel.ERROR,
        ),
        # Métricas
        TelemetrySignal(
            signal_type=SignalType.METRIC, service="database",
            message="query_duration_seconds=7.5",
            timestamp=base_time + timedelta(milliseconds=7650),
            trace_id=trace_id, value=7.5, unit="seconds",
            labels={"query": "SELECT_users", "status": "slow"},
        ),
        TelemetrySignal(
            signal_type=SignalType.METRIC, service="database",
            message="active_connections=98",
            timestamp=base_time + timedelta(seconds=1),
            value=98.0, unit="connections",
            labels={"pool_max": "100"},
        ),
        TelemetrySignal(
            signal_type=SignalType.METRIC, service="api-gateway",
            message="http_request_duration_seconds=8.5 (p99)",
            timestamp=base_time + timedelta(seconds=9),
            value=8.5, unit="seconds",
            labels={"method": "POST", "path": "/checkout", "status": "504"},
        ),
    ]

    return trace_id, spans, signals


def display_isolated_view(signals: list[TelemetrySignal]) -> None:
    """Mostra como seria investigar com ferramentas isoladas (sem correlação)."""
    print("\n" + "─" * 70)
    print("📊 VISÃO ISOLADA (ferramentas separadas)")
    print("─" * 70)

    metrics = [s for s in signals if s.signal_type == SignalType.METRIC]
    logs = [s for s in signals if s.signal_type == SignalType.LOG]

    print("\n  📈 Painel de Métricas (Grafana/Prometheus):")
    for m in metrics:
        print(f"    {m}")

    print("\n  📝 Painel de Logs (Elasticsearch/Loki):")
    for l_signal in logs:
        print(f"    {l_signal}")

    print("\n  ❓ PROBLEMA:")
    print("     Engenheiro precisa abrir 3 ferramentas diferentes")
    print("     Copiar trace IDs manualmente entre dashboards")
    print("     Correlacionar timestamps mentalmente")
    print("     → Tempo estimado de diagnóstico: 25-40 minutos")


def display_correlated_view(
    trace_id: str, spans: list[TraceSpan], signals: list[TelemetrySignal]
) -> None:
    """Mostra a visão correlacionada com trace_id como elo de ligação."""
    print("\n" + "─" * 70)
    print(f"🔗 VISÃO CORRELACIONADA (trace_id: {trace_id[:8]}...)")
    print("─" * 70)

    print("\n  🌳 TRACE TREE (waterfall):")
    indent_map = {None: 0}
    for span in spans:
        depth = indent_map.get(span.parent_span_id, 0)
        indent_map[span.span_id] = depth + 1
        prefix = "  │  " * depth + "  ├─ "
        status_icon = "✅" if span.status_code < 400 else "⚠️" if span.status_code < 500 else "❌"
        bar_len = min(int(span.duration_ms / 200), 40)
        bar = "█" * max(bar_len, 1)
        print(
            f"    {prefix}{status_icon} {span.service}/{span.operation} "
            f"[{span.duration_ms:.0f}ms] {bar}"
        )

    print("\n  📋 SINAIS CORRELACIONADOS AO TRACE (timeline unificada):")
    correlated = sorted(
        [s for s in signals if s.trace_id == trace_id],
        key=lambda s: s.timestamp,
    )
    for s in correlated:
        icon = "📈" if s.signal_type == SignalType.METRIC else "📝"
        print(f"    {icon} {s}")

    print("\n  🎯 DIAGNÓSTICO AUTOMÁTICO:")
    print(f"     1. Trace revela: 88% do tempo total gasto em database/SELECT")
    print(f"     2. Log correlacionado confirma: query sem índice (7500ms)")
    print(f"     3. Métrica associada mostra: connection pool em 98/100")
    print(f"     4. Cadeia de impacto: DB → user-service → cart → payment → gateway")
    print(f"     → Tempo de diagnóstico: ~3 minutos")


def run_demo() -> None:
    print("=" * 70)
    print("🔬 Demo: Métricas, Logs e Traces no Troubleshooting Moderno")
    print("   Curso 3 — Observabilidade Inteligente")
    print("=" * 70)

    trace_id, spans, signals = generate_trace_scenario()

    # Visão 1: Ferramentas isoladas
    display_isolated_view(signals)

    # Visão 2: Correlação por trace_id
    display_correlated_view(trace_id, spans, signals)

    # Resumo
    print("\n" + "=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  A correlação via trace_id transforma três fontes de dados separadas
  em uma narrativa unificada de cada requisição. Ao invés de investigar
  métricas, logs e traces separadamente, o engenheiro navega por um
  fluxo contínuo que conta a história completa da falha.

  Na Aula 1.3, veremos como o contexto operacional (deploys, configs)
  enriquece ainda mais essa correlação.
    """)


if __name__ == "__main__":
    run_demo()
