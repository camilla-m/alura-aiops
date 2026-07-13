"""
Vídeo 1.4 — OpenTelemetry e padronização de observabilidade
============================================================
Simula a arquitetura do OpenTelemetry Collector, demonstrando
o fluxo de dados desde a instrumentação até a exportação
para múltiplos backends, de forma vendor-agnostic.

Conceitos demonstrados:
- Arquitetura do OpenTelemetry (APIs, SDKs, Collector)
- Pipeline: receivers → processors → exporters
- OTLP (OpenTelemetry Protocol)
- Instrumentação automática vs. manual
- Independência de vendor (multi-backend)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class TelemetryType(str, Enum):
    TRACES  = "traces"
    METRICS = "metrics"
    LOGS    = "logs"


class ComponentType(str, Enum):
    RECEIVER  = "receiver"
    PROCESSOR = "processor"
    EXPORTER  = "exporter"


@dataclass
class TelemetryData:
    """Dado de telemetria fluindo pelo pipeline do Collector."""
    data_type: TelemetryType
    source: str
    payload: dict
    resource_attributes: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return (
            f"[{self.data_type.value:7}] "
            f"from={self.source} "
            f"attrs={self.resource_attributes}"
        )


@dataclass
class PipelineComponent:
    """Componente do pipeline do OTel Collector."""
    name: str
    component_type: ComponentType
    config: dict = field(default_factory=dict)

    def process(self, data: TelemetryData) -> Optional[TelemetryData]:
        """Processa o dado de telemetria (simulado)."""
        return data


class OTelReceiver(PipelineComponent):
    """Receptor — recebe dados de telemetria de diversas fontes."""

    def __init__(self, name: str, protocol: str, port: int):
        super().__init__(
            name=name,
            component_type=ComponentType.RECEIVER,
            config={"protocol": protocol, "port": port},
        )

    def receive(self, data: TelemetryData) -> TelemetryData:
        print(f"    📥 [{self.name}] Recebendo {data.data_type.value} via "
              f"{self.config['protocol']}:{self.config['port']} de {data.source}")
        return data


class OTelProcessor(PipelineComponent):
    """Processador — transforma, filtra ou enriquece dados."""

    def __init__(self, name: str, action: str):
        super().__init__(
            name=name,
            component_type=ComponentType.PROCESSOR,
            config={"action": action},
        )

    def process(self, data: TelemetryData) -> Optional[TelemetryData]:
        action = self.config["action"]

        if action == "batch":
            print(f"    ⚙️  [{self.name}] Agrupando em batch (200ms / 512 itens)")
        elif action == "filter":
            if data.payload.get("level") == "DEBUG":
                print(f"    ⚙️  [{self.name}] Filtrando: descartando log DEBUG")
                return None
            print(f"    ⚙️  [{self.name}] Filtro OK — dado mantido")
        elif action == "enrich":
            data.resource_attributes.update({
                "k8s.namespace": "production",
                "k8s.pod.name": f"{data.source}-pod-abc123",
                "cloud.provider": "aws",
                "cloud.region": "us-east-1",
            })
            print(f"    ⚙️  [{self.name}] Enriquecendo com metadata K8s/Cloud")
        elif action == "tail_sampling":
            is_error = data.payload.get("status_code", 200) >= 400
            if is_error:
                print(f"    ⚙️  [{self.name}] Tail sampling: RETENDO trace (contém erro)")
            else:
                print(f"    ⚙️  [{self.name}] Tail sampling: amostrando 10%")

        return data


class OTelExporter(PipelineComponent):
    """Exportador — envia dados para backends de observabilidade."""

    def __init__(self, name: str, backend: str, endpoint: str):
        super().__init__(
            name=name,
            component_type=ComponentType.EXPORTER,
            config={"backend": backend, "endpoint": endpoint},
        )

    def export(self, data: TelemetryData) -> None:
        print(f"    📤 [{self.name}] Exportando {data.data_type.value} "
              f"→ {self.config['backend']} ({self.config['endpoint']})")


@dataclass
class OTelCollector:
    """Simulação do OpenTelemetry Collector com pipelines configuráveis."""
    receivers: list[OTelReceiver] = field(default_factory=list)
    processors: list[OTelProcessor] = field(default_factory=list)
    exporters: list[OTelExporter] = field(default_factory=list)

    def process_pipeline(self, data: TelemetryData) -> None:
        """Processa um dado através de todo o pipeline."""
        current = data

        # Receivers
        for receiver in self.receivers:
            if receiver.config.get("protocol") in ("otlp", "grpc", "http"):
                current = receiver.receive(current)
                break

        # Processors (em cadeia)
        for processor in self.processors:
            if current is None:
                print(f"    🚫 Dado descartado no processador {processor.name}")
                return
            current = processor.process(current)

        if current is None:
            return

        # Exporters (fan-out para múltiplos backends)
        for exporter in self.exporters:
            exporter.export(current)


def build_collector() -> OTelCollector:
    """Constrói um OTel Collector com configuração realista."""
    return OTelCollector(
        receivers=[
            OTelReceiver("otlp-grpc", "grpc", 4317),
            OTelReceiver("otlp-http", "http", 4318),
            OTelReceiver("prometheus", "http", 8888),
        ],
        processors=[
            OTelProcessor("resource-enricher", "enrich"),
            OTelProcessor("log-filter", "filter"),
            OTelProcessor("batch", "batch"),
            OTelProcessor("tail-sampler", "tail_sampling"),
        ],
        exporters=[
            OTelExporter("otlp-datadog", "Datadog", "https://api.datadoghq.com/v1"),
            OTelExporter("otlp-grafana", "Grafana Cloud", "https://otlp.grafana.net"),
            OTelExporter("debug-console", "Console (debug)", "stdout"),
        ],
    )


def print_architecture() -> None:
    """Exibe a arquitetura do OpenTelemetry de forma visual."""
    print("""
  ┌─────────────────────────────────────────────────────────────────┐
  │                    ARQUITETURA OPENTELEMETRY                    │
  ├─────────────────────────────────────────────────────────────────┤
  │                                                                 │
  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
  │  │  App Python  │  │  App Java   │  │  App Go     │  ← SDKs   │
  │  │  (OTel SDK)  │  │  (OTel SDK) │  │  (OTel SDK) │            │
  │  └──────┬───────┘  └──────┬──────┘  └──────┬──────┘            │
  │         │                 │                 │                   │
  │         └────────────┬────┘────────────────┘                    │
  │                      │ OTLP (gRPC/HTTP)                        │
  │                      ▼                                          │
  │  ┌──────────────────────────────────────────────┐              │
  │  │          OPENTELEMETRY COLLECTOR              │              │
  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐     │              │
  │  │  │ Receivers│→│Processors│→│ Exporters│     │              │
  │  │  │ (OTLP,   │ │(batch,   │ │(Datadog, │     │              │
  │  │  │  Prom,   │ │ filter,  │ │ Grafana, │     │              │
  │  │  │  Jaeger) │ │ enrich)  │ │ Jaeger)  │     │              │
  │  │  └──────────┘ └──────────┘ └──────────┘     │              │
  │  └──────────────────────────────────────────────┘              │
  │                      │                                          │
  │         ┌────────────┼────────────┐                            │
  │         ▼            ▼            ▼                            │
  │  ┌───────────┐ ┌──────────┐ ┌──────────┐                     │
  │  │  Datadog  │ │ Grafana  │ │  Jaeger  │  ← Backends          │
  │  │  Cloud    │ │  Cloud   │ │          │                       │
  │  └───────────┘ └──────────┘ └──────────┘                     │
  │                                                                 │
  └─────────────────────────────────────────────────────────────────┘
    """)


def run_demo() -> None:
    print("=" * 70)
    print("🔧 Demo: OpenTelemetry — Padronização de Observabilidade")
    print("   Curso 3 — Observabilidade Inteligente")
    print("=" * 70)

    print_architecture()

    collector = build_collector()

    # Configuração YAML do Collector (referência)
    print("─" * 70)
    print("📝 CONFIGURAÇÃO DO COLLECTOR (otel-collector-config.yaml)")
    print("─" * 70)
    print("""
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317
        http:
          endpoint: 0.0.0.0:4318

  processors:
    batch:
      timeout: 200ms
      send_batch_size: 512
    filter:
      logs:
        exclude:
          match_type: strict
          severity_texts: ["DEBUG"]
    resource:
      attributes:
        - key: k8s.namespace
          action: upsert
          value: production

  exporters:
    otlp/datadog:
      endpoint: https://api.datadoghq.com/v1
    otlp/grafana:
      endpoint: https://otlp.grafana.net
    debug:
      verbosity: detailed

  service:
    pipelines:
      traces:
        receivers: [otlp]
        processors: [batch, resource]
        exporters: [otlp/datadog, otlp/grafana]
      metrics:
        receivers: [otlp]
        processors: [batch]
        exporters: [otlp/datadog, otlp/grafana]
      logs:
        receivers: [otlp]
        processors: [filter, batch]
        exporters: [otlp/grafana, debug]
    """)

    # Simular fluxo de dados
    print("─" * 70)
    print("🔄 SIMULAÇÃO DO PIPELINE (processando dados de telemetria)")
    print("─" * 70)

    sample_data = [
        TelemetryData(
            data_type=TelemetryType.TRACES,
            source="checkout-service",
            payload={"operation": "processPayment", "duration_ms": 350, "status_code": 500},
            resource_attributes={"service.name": "checkout-service", "service.version": "v2.8.0"},
        ),
        TelemetryData(
            data_type=TelemetryType.LOGS,
            source="user-service",
            payload={"message": "ERROR: timeout connecting to DB", "level": "ERROR"},
            resource_attributes={"service.name": "user-service"},
        ),
        TelemetryData(
            data_type=TelemetryType.LOGS,
            source="api-gateway",
            payload={"message": "Health check OK", "level": "DEBUG"},
            resource_attributes={"service.name": "api-gateway"},
        ),
        TelemetryData(
            data_type=TelemetryType.METRICS,
            source="database",
            payload={"name": "db.connections.active", "value": 95},
            resource_attributes={"service.name": "database"},
        ),
    ]

    for i, data in enumerate(sample_data, 1):
        print(f"\n  📦 Dado #{i}: {data}")
        collector.process_pipeline(data)
        time.sleep(0.1)

    print("\n" + "=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  O OpenTelemetry padroniza a coleta de telemetria de forma que:

  1. INSTRUMENTAÇÃO: SDKs disponíveis para todas as linguagens principais
  2. COLETA:         Collector unificado com pipeline configurável
  3. EXPORTAÇÃO:     Dados vão para qualquer backend (vendor-agnostic)
  4. PROCESSAMENTO:  Enriquecimento, filtragem e amostragem no Collector

  Benefício principal: Mudar de Datadog para Grafana (ou usar ambos)
  sem alterar uma linha de código na aplicação.

  Na Aula 1.5 (Hands-on), vamos usar esses conceitos para investigar
  um microsserviço com falha usando múltiplos sinais correlacionados.
    """)


if __name__ == "__main__":
    run_demo()
