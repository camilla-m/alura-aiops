"""
Vídeo 2.3 — Argo Rollouts: o Rollout e o AnalysisTemplate na prática
=====================================================================
Gera manifests REAIS do Argo Rollouts (apiVersion argoproj.io/v1alpha1)
para um deploy canário e depois SIMULA localmente a execução dos steps,
chamando uma análise a cada gate para decidir promover ou abortar.

Estratégia canária definida:
    setWeight 20 → pause → setWeight 50 → analysis → setWeight 100

Conceitos demonstrados:
- Recurso Rollout: canary strategy com steps (setWeight / pause / analysis)
- AnalysisTemplate: métricas + successCondition que aprovam cada gate
- Como o controller avança ou aborta o rollout a partir da análise
- Ponte entre o YAML declarativo e o que acontece em runtime

Rodar de verdade (fora deste simulador) seria, num cluster com o
controller instalado:
    kubectl apply -f rollout.yaml -f analysis-template.yaml
    kubectl argo rollouts get rollout mapi-api --watch
"""

import random
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

random.seed(42)

APP = "mapi-api"
NAMESPACE = "production"
IMAGE_NEW = "registry.storyblok.com/mapi-api:v2.4.2"


class Resultado(str, Enum):
    RUNNING = "▶️  RUNNING"
    PROMOTED = "✅ PROMOTED"
    ABORTED = "❌ ABORTED"


@dataclass
class Step:
    """Um step da estratégia canária do Rollout."""
    tipo: str            # setWeight | pause | analysis
    valor: object = None  # peso (int), duração (str) ou nome do template


# ---------------------------------------------------------------------------
# Geração dos manifests REAIS do Argo Rollouts
# ---------------------------------------------------------------------------

def gerar_rollout_yaml(steps: list[Step]) -> str:
    """Monta o YAML do recurso Rollout com a estratégia canária."""
    linhas_steps: list[str] = []
    for s in steps:
        if s.tipo == "setWeight":
            linhas_steps.append(f"        - setWeight: {s.valor}")
        elif s.tipo == "pause":
            if s.valor:
                linhas_steps.append(f"        - pause: {{duration: {s.valor}}}")
            else:
                linhas_steps.append("        - pause: {}")
        elif s.tipo == "analysis":
            linhas_steps.append("        - analysis:")
            linhas_steps.append("            templates:")
            linhas_steps.append(f"              - templateName: {s.valor}")
            linhas_steps.append("            args:")
            linhas_steps.append("              - name: service-name")
            linhas_steps.append(f"                value: {APP}")
    steps_bloco = "\n".join(linhas_steps)

    return f"""apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: {APP}
  namespace: {NAMESPACE}
spec:
  replicas: 5
  revisionHistoryLimit: 3
  selector:
    matchLabels:
      app: {APP}
  template:
    metadata:
      labels:
        app: {APP}
    spec:
      containers:
        - name: {APP}
          image: {IMAGE_NEW}
          ports:
            - containerPort: 8080
  strategy:
    canary:
      canaryService: {APP}-canary
      stableService: {APP}-stable
      trafficRouting:
        nginx:
          stableIngress: {APP}-ingress
      steps:
{steps_bloco}
"""


def gerar_analysis_template_yaml() -> str:
    """
    AnalysisTemplate que aprova o gate: taxa de sucesso >= 95% e
    latência p95 < 300ms, medidas via Prometheus a cada intervalo.
    failureLimit: 2 => aborta após 2 medições fora do critério.

    Escrito como template com o marcador __NS__ para evitar conflito
    entre as chaves do PromQL/Argo ({{args...}}) e o f-string do Python.
    """
    template = """apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: canary-success-rate
  namespace: __NS__
spec:
  args:
    - name: service-name
  metrics:
    - name: success-rate
      interval: 1m
      count: 3
      successCondition: result >= 0.95
      failureLimit: 2
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: >
            sum(rate(http_requests_total{service="{{args.service-name}}",status!~"5.."}[1m]))
            /
            sum(rate(http_requests_total{service="{{args.service-name}}"}[1m]))
    - name: latency-p95
      interval: 1m
      count: 3
      successCondition: result < 300
      failureLimit: 2
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: >
            histogram_quantile(0.95,
              sum(rate(http_request_duration_ms_bucket{service="{{args.service-name}}"}[1m])) by (le))
"""
    return template.replace("__NS__", NAMESPACE)


# ---------------------------------------------------------------------------
# Simulação local da execução dos steps
# ---------------------------------------------------------------------------

@dataclass
class AnaliseFake:
    """Emula o que o AnalysisTemplate mediria no cluster naquele gate."""
    success_rate: float
    latency_p95: float

    @property
    def aprovado(self) -> bool:
        return self.success_rate >= 0.95 and self.latency_p95 < 300


def medir_gate(saudavel: bool) -> AnaliseFake:
    """Gera a 'leitura' do Prometheus para o gate de análise."""
    if saudavel:
        return AnaliseFake(random.uniform(0.97, 0.995), random.uniform(180, 270))
    return AnaliseFake(random.uniform(0.86, 0.93), random.uniform(320, 480))


def simular_rollout(steps: list[Step], canary_saudavel: bool) -> Resultado:
    print(f"\n{'─' * 70}")
    titulo = "canary SAUDÁVEL" if canary_saudavel else "canary DEGRADADO"
    print(f"  ▶️  Simulando execução dos steps ({titulo})")
    print(f"{'─' * 70}")
    peso = 0
    for i, s in enumerate(steps, 1):
        if s.tipo == "setWeight":
            peso = s.valor
            print(f"  [step {i}] setWeight {peso}%  → canary recebe {peso}% do tráfego")
        elif s.tipo == "pause":
            dur = s.valor or "até intervenção manual"
            print(f"  [step {i}] pause ({dur})  → janela de observação")
        elif s.tipo == "analysis":
            leitura = medir_gate(canary_saudavel)
            print(f"  [step {i}] analysis '{s.valor}' no peso {peso}%:")
            print(f"            success-rate = {leitura.success_rate*100:.1f}% "
                  f"(gate: >= 95%)")
            print(f"            latency-p95  = {leitura.latency_p95:.0f}ms "
                  f"(gate: < 300ms)")
            if not leitura.aprovado:
                print(f"            → 🚨 análise REPROVOU o gate")
                print(f"\n  {Resultado.ABORTED.value}: controller reverte para o stable "
                      f"(peso volta a 0%)")
                return Resultado.ABORTED
            print(f"            → análise aprovou, seguindo para o próximo step")
    print(f"\n  {Resultado.PROMOTED.value}: canary atingiu 100% e virou o novo stable")
    return Resultado.PROMOTED


def executar() -> None:
    print("=" * 70)
    print("🚀 Argo Rollouts: Rollout + AnalysisTemplate")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)

    steps = [
        Step("setWeight", 20),
        Step("pause", "2m"),
        Step("setWeight", 50),
        Step("analysis", "canary-success-rate"),
        Step("setWeight", 100),
    ]

    rollout_yaml = gerar_rollout_yaml(steps)
    analysis_yaml = gerar_analysis_template_yaml()

    print("\n📄 rollout.yaml (kind: Rollout — argoproj.io/v1alpha1)")
    print("─" * 70)
    print(rollout_yaml)
    print("📄 analysis-template.yaml (kind: AnalysisTemplate)")
    print("─" * 70)
    print(analysis_yaml)

    # Salva os manifests ao lado do script (idempotente)
    destino = Path(__file__).parent
    (destino / "rollout.yaml").write_text(rollout_yaml)
    (destino / "analysis-template.yaml").write_text(analysis_yaml)
    print(f"💾 Manifests salvos em: {destino}")
    print("   Num cluster real: kubectl apply -f rollout.yaml -f analysis-template.yaml")
    print("   Acompanhar:        kubectl argo rollouts get rollout mapi-api --watch")

    print("\n" + "=" * 70)
    print("🎬 SIMULAÇÃO DA EXECUÇÃO DOS STEPS")
    print("=" * 70)
    r_ok = simular_rollout(steps, canary_saudavel=True)
    r_bad = simular_rollout(steps, canary_saudavel=False)

    print("\n" + "=" * 70)
    print("💡 CONCLUSÃO")
    print("=" * 70)
    print(f"""
  Canary saudável  → {r_ok.value}
  Canary degradado → {r_bad.value}

  O mesmo YAML declarativo produz dois desfechos: quem decide é a análise
  no gate, não o pipeline. O controller do Argo Rollouts avança os steps
  quando a análise passa e faz rollback automático quando ela falha.

  ➡️  Próximo vídeo (2.4): rollback inteligente por janelas de métricas.
    """)


if __name__ == "__main__":
    executar()
