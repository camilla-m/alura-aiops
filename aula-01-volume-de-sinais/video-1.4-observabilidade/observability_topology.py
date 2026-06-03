"""
Vídeo 1.4 — Observabilidade operacional em ambientes distribuídos
=================================================================
Demonstra como os três pilares da observabilidade se conectam
em tempo real para fornecer visibilidade completa de um sistema
distribuído durante um incidente.

Conceitos demonstrados:
- Propagação de trace_id entre serviços
- Correlação de logs + métricas + traces via correlation ID
- Mapa de topologia de serviços
- Exemplos de instrumentação com OpenTelemetry
"""

from __future__ import annotations

import uuid
import time
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Instrumentação simplificada (simula OpenTelemetry)
# ---------------------------------------------------------------------------

@dataclass
class Span:
    """Representa um span de distributed tracing."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    service: str
    operation: str
    start_time: datetime
    duration_ms: float
    status: str  # "OK" | "ERROR"
    attributes: dict = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class MetricPoint:
    """Representa um ponto de métrica com contexto de trace."""
    service: str
    metric_name: str
    value: float
    trace_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    labels: dict = field(default_factory=dict)


@dataclass
class LogEntry:
    """Representa uma entrada de log estruturado."""
    service: str
    level: str
    message: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    fields: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Simulador de requisição distribuída com instrumentação completa
# ---------------------------------------------------------------------------

class ObservabilityContext:
    """
    Coleta todos os sinais gerados durante a vida de uma requisição.
    Simula o que um backend de observabilidade (Grafana/Datadog) armazenaria.
    """

    def __init__(self):
        self.traces: list[Span] = []
        self.metrics: list[MetricPoint] = []
        self.logs: list[LogEntry] = []

    def record_span(self, span: Span) -> None:
        self.traces.append(span)

    def record_metric(self, metric: MetricPoint) -> None:
        self.metrics.append(metric)

    def record_log(self, log: LogEntry) -> None:
        self.logs.append(log)

    def correlate_by_trace(self, trace_id: str) -> dict:
        """
        Correlaciona todos os sinais de uma requisição pelo trace_id.
        Isso é exatamente o que plataformas como Datadog APM fazem.
        """
        return {
            "trace_id": trace_id,
            "spans": [s for s in self.traces if s.trace_id == trace_id],
            "metrics": [m for m in self.metrics if m.trace_id == trace_id],
            "logs": [l for l in self.logs if l.trace_id == trace_id],
        }


def simulate_distributed_request(
    ctx: ObservabilityContext,
    inject_failure: bool = False
) -> str:
    """
    Simula uma requisição passando por:
    api-gateway → auth-service → product-service → database

    Todos os sinais são instrumentados com o mesmo trace_id.
    """
    trace_id = str(uuid.uuid4())[:8]
    print(f"\n  🔗 Trace ID: {trace_id} | Failure: {inject_failure}")
    print(f"  {'─'*55}")

    def make_span(service: str, operation: str, parent_id: Optional[str],
                  latency: float, error: Optional[str] = None) -> Span:
        span_id = str(uuid.uuid4())[:6]
        status = "ERROR" if error else "OK"
        span = Span(
            trace_id=trace_id, span_id=span_id,
            parent_span_id=parent_id, service=service,
            operation=operation, start_time=datetime.now(),
            duration_ms=latency, status=status, error=error,
        )
        ctx.record_span(span)

        # Log estruturado com trace context
        ctx.record_log(LogEntry(
            service=service, level="ERROR" if error else "INFO",
            message=f"{operation} {'FAILED: ' + error if error else 'completed'}",
            trace_id=trace_id, span_id=span_id,
            fields={"latency_ms": latency, "status": status},
        ))

        # Métrica com trace context
        ctx.record_metric(MetricPoint(
            service=service, metric_name="request_duration_ms",
            value=latency, trace_id=trace_id,
            labels={"operation": operation, "status": status},
        ))

        print(f"  [{service:<18}] {operation:<30} {latency:>6.0f}ms  {'❌' if error else '✅'}")
        return span

    # api-gateway recebe a requisição
    gw_span = make_span("api-gateway", "HTTP GET /api/products", None, 12.0)

    # auth-service valida o token
    auth_error = "DB connection timeout" if inject_failure else None
    auth_span = make_span("auth-service", "validate_token", gw_span.span_id,
                          500.0 if inject_failure else 45.0, auth_error)

    if inject_failure:
        # database — simula a falha real
        make_span("database", "SELECT sessions", auth_span.span_id, 30_000.0,
                  "Connection pool exhausted")
        # gateway recebe upstream error
        make_span("api-gateway", "upstream_error_handler", gw_span.span_id, 30_100.0,
                  "auth-service timeout")
    else:
        # product-service busca dados (caminho feliz)
        prod_span = make_span("product-service", "get_product_list", gw_span.span_id, 38.0)
        make_span("database", "SELECT products WHERE active=1", prod_span.span_id, 22.0)

    return trace_id


def print_correlation_report(ctx: ObservabilityContext, trace_id: str) -> None:
    """Exibe o relatório de correlação dos 3 pilares para um trace_id."""
    data = ctx.correlate_by_trace(trace_id)

    print(f"\n  {'='*55}")
    print(f"  📊 CORRELAÇÃO DOS 3 PILARES — Trace {trace_id}")
    print(f"  {'='*55}")

    errors = [s for s in data["spans"] if s.status == "ERROR"]
    total_duration = sum(s.duration_ms for s in data["spans"] if not s.parent_span_id)

    print(f"\n  📍 TRACES  ({len(data['spans'])} spans)")
    for span in data["spans"]:
        indent = "   └─" if span.parent_span_id else "   ●"
        err = f" ← {span.error}" if span.error else ""
        print(f"  {indent} [{span.service}] {span.operation} ({span.duration_ms:.0f}ms){err}")

    print(f"\n  📝 LOGS    ({len(data['logs'])} entradas)")
    for log in data["logs"]:
        icon = "🔴" if log.level == "ERROR" else "🟢"
        print(f"  {icon}  [{log.service}] {log.message}")

    print(f"\n  📈 MÉTRICAS ({len(data['metrics'])} pontos)")
    for m in data["metrics"]:
        print(f"    {m.service}.{m.metric_name} = {m.value:.0f} [{m.labels.get('status')}]")

    print(f"\n  ⏱️  Latência total da requisição: {total_duration:.0f}ms")
    if errors:
        print(f"  ❌  Spans com erro: {len(errors)}")
        print(f"  🎯  Serviço raiz do erro: {errors[0].service}")


if __name__ == "__main__":
    print("🔬 Demo: Observabilidade Operacional — Os 3 Pilares Conectados")
    print("     Nível 1 — AIOps & Automação de Incidentes")

    ctx = ObservabilityContext()

    print("\n" + "=" * 60)
    print("CENÁRIO 1: Requisição sem falha (caminho feliz)")
    print("=" * 60)
    trace_ok = simulate_distributed_request(ctx, inject_failure=False)
    print_correlation_report(ctx, trace_ok)

    print("\n" + "=" * 60)
    print("CENÁRIO 2: Requisição com falha de banco de dados")
    print("=" * 60)
    trace_fail = simulate_distributed_request(ctx, inject_failure=True)
    print_correlation_report(ctx, trace_fail)

    print("\n" + "=" * 60)
    print("📌 CONCLUSÃO")
    print("=" * 60)
    print("""
  Com o trace_id propagado por todos os serviços, conseguimos
  correlacionar instantaneamente os 3 pilares da observabilidade
  para um único request — reduzindo o MTTR drasticamente.

  Sem esse contexto compartilhado, cada equipe veria apenas
  a sua parte do problema, dificultando o diagnóstico correto.
    """)
