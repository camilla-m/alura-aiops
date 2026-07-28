"""
Vídeo 5.2 — Argo Rollouts: AnalysisTemplate e Experiment
=========================================================
Funcionalidades avançadas do Argo Rollouts. Este script GERA os
manifestos YAML reais (apiVersion: argoproj.io/v1alpha1) de um
AnalysisTemplate com múltiplas métricas consultando Prometheus e de
um Experiment que roda baseline vs. canary em paralelo, e depois
SIMULA a avaliação das métricas decidindo promover ou abortar.

O que é do Argo Rollouts (real):
- É um controller do Kubernetes que substitui o Deployment por um
  recurso Rollout com estratégias canary/blue-green.
- Um AnalysisTemplate declara métricas (query + successCondition +
  failureCondition + failureLimit). Durante o canary, o controller
  cria um AnalysisRun que consulta o provider (aqui, Prometheus).
- Se failureLimit é excedido, o Rollout é abortado automaticamente.
- Um Experiment sobe ReplicaSets baseline e canary temporários para
  comparar as duas versões sob o mesmo tráfego/condições.

Conceitos demonstrados:
- Geração de YAML v1alpha1 fiel (AnalysisTemplate + Experiment)
- Métricas successRate e p95 latency com queries PromQL
- Simulação de AnalysisRun: measurement -> Successful/Failed
- failureLimit → decisão de promover (Healthy) ou abortar (Degraded)
"""

import random
from dataclasses import dataclass, field
from enum import Enum

random.seed(42)


# ---------------------------------------------------------------------------
# 1) Manifestos reais (apiVersion: argoproj.io/v1alpha1)
# ---------------------------------------------------------------------------

ANALYSIS_TEMPLATE_YAML = """\
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: checkout-api-analysis
spec:
  args:
    - name: service-name
  metrics:
    - name: success-rate
      interval: 30s
      count: 5
      successCondition: result[0] >= 0.99
      failureCondition: result[0] < 0.95
      failureLimit: 2
      provider:
        prometheus:
          address: http://prometheus.monitoring.svc:9090
          query: |
            sum(rate(http_requests_total{
              service="{{args.service-name}}", code!~"5.."}[2m]))
            /
            sum(rate(http_requests_total{
              service="{{args.service-name}}"}[2m]))
    - name: p95-latency-ms
      interval: 30s
      count: 5
      successCondition: result[0] <= 300
      failureCondition: result[0] > 500
      failureLimit: 2
      provider:
        prometheus:
          address: http://prometheus.monitoring.svc:9090
          query: |
            histogram_quantile(0.95, sum(rate(
              http_request_duration_seconds_bucket{
                service="{{args.service-name}}"}[2m])) by (le)) * 1000
"""

EXPERIMENT_YAML = """\
apiVersion: argoproj.io/v1alpha1
kind: Experiment
metadata:
  name: baseline-vs-canary
spec:
  duration: 5m
  templates:
    - name: baseline
      replicas: 2
      selector:
        matchLabels: {app: checkout-api}
      template:
        spec:
          containers:
            - name: checkout-api
              image: registry.example.com/checkout-api:stable
    - name: canary
      replicas: 2
      selector:
        matchLabels: {app: checkout-api}
      template:
        spec:
          containers:
            - name: checkout-api
              image: registry.example.com/checkout-api:v3.2.0
  analyses:
    - name: success-rate
      templateName: checkout-api-analysis
      args:
        - name: service-name
          value: checkout-api-canary
"""


# ---------------------------------------------------------------------------
# 2) Simulação do AnalysisRun
# ---------------------------------------------------------------------------

class Phase(str, Enum):
    SUCCESSFUL = "✅ Successful"
    FAILED = "❌ Failed"
    INCONCLUSIVE = "🟡 Inconclusive"


@dataclass
class Metric:
    name: str
    count: int
    failure_limit: int
    success_ok: "callable"   # result -> bool (successCondition)
    failure_bad: "callable"  # result -> bool (failureCondition)
    sampler: "callable"      # () -> float (valor medido)
    measurements: list[float] = field(default_factory=list)
    failures: int = 0
    phase: Phase = Phase.INCONCLUSIVE

    def run(self) -> None:
        for _ in range(self.count):
            value = self.sampler()
            self.measurements.append(value)
            if self.failure_bad(value):
                self.failures += 1
                if self.failures > self.failure_limit:
                    self.phase = Phase.FAILED
                    return
        # Se nenhuma medição violou o failureLimit, aprova se a última satisfaz o sucesso
        self.phase = Phase.SUCCESSFUL if self.success_ok(self.measurements[-1]) else Phase.INCONCLUSIVE


def make_metrics(healthy: bool) -> list[Metric]:
    """Cria as duas métricas do AnalysisTemplate para um cenário saudável ou degradado."""
    if healthy:
        sr_sampler = lambda: random.uniform(0.990, 0.999)
        lat_sampler = lambda: random.uniform(210, 290)
    else:
        sr_sampler = lambda: random.uniform(0.930, 0.970)
        lat_sampler = lambda: random.uniform(480, 620)
    return [
        Metric(
            name="success-rate", count=5, failure_limit=2,
            success_ok=lambda r: r >= 0.99, failure_bad=lambda r: r < 0.95,
            sampler=sr_sampler,
        ),
        Metric(
            name="p95-latency-ms", count=5, failure_limit=2,
            success_ok=lambda r: r <= 300, failure_bad=lambda r: r > 500,
            sampler=lat_sampler,
        ),
    ]


def evaluate(scenario: str, healthy: bool) -> None:
    print("\n" + "─" * 70)
    print(f"🧪 AnalysisRun — cenário '{scenario}'")
    print("─" * 70)
    metrics = make_metrics(healthy)
    for m in metrics:
        m.run()
        series = ", ".join(f"{v:.3f}" if v < 10 else f"{v:.0f}" for v in m.measurements)
        print(f"  {m.name:<16} measurements=[{series}]")
        print(f"  {'':<16} failures={m.failures}/{m.failure_limit} (limite) → {m.phase.value}")

    aborted = any(m.phase is Phase.FAILED for m in metrics)
    if aborted:
        print("\n  🔴 AnalysisRun: Failed → Rollout status = Degraded")
        print("     $ kubectl argo rollouts abort checkout-api  (automático)")
        print("     Tráfego revertido para a versão stable.")
    else:
        print("\n  🟢 AnalysisRun: Successful → Rollout prossegue para o próximo passo")
        print("     $ kubectl argo rollouts promote checkout-api")
        print("     Canary avança de 25% → 50% → 100% do tráfego.")


def run_demo() -> None:
    print("=" * 70)
    print("⎈ Argo Rollouts — AnalysisTemplate & Experiment")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)

    print("\n📄 Manifesto 1 — AnalysisTemplate (multi-métrica, Prometheus):")
    print("─" * 70)
    print(ANALYSIS_TEMPLATE_YAML)

    print("📄 Manifesto 2 — Experiment (baseline vs. canary em paralelo):")
    print("─" * 70)
    print(EXPERIMENT_YAML)

    print("=" * 70)
    print("🔎 Simulação da avaliação (o controller consultaria o Prometheus)")
    print("=" * 70)
    evaluate("v3.2.0 saudável", healthy=True)
    evaluate("v3.2.0 com regressão", healthy=False)

    print("\n" + "=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  O AnalysisTemplate transforma métricas do Prometheus em gates
  declarativos: successCondition/failureCondition julgam cada medição
  e o failureLimit define quanta instabilidade tolerar antes de abortar.
  O Experiment isola baseline e canary para uma comparação justa.
  Tudo versionado como YAML, aplicado com kubectl argo rollouts.

  No Vídeo 5.3, saímos do deploy e vamos ao runtime: feature flags
  estilo LaunchDarkly para ligar/desligar comportamento sem redeploy.
    """)


if __name__ == "__main__":
    run_demo()
