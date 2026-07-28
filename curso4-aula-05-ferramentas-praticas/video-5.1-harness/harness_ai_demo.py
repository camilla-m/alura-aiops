"""
Vídeo 5.1 — Harness: Continuous Verification e governance gates
================================================================
Reproduz o conceito de Continuous Verification (CV) do Harness:
após um deploy, a plataforma verifica automaticamente as métricas
(erro, latência, logs) do canary contra uma janela de baseline,
calcula um risk score e aplica governance gates que decidem entre
auto-approve, hold para aprovação manual ou rollback automático.

O que é do Harness (real):
- CV coleta métricas de um "Health Source" (Prometheus, Datadog,
  AppDynamics, New Relic, CloudWatch...) durante uma janela pós-deploy.
- Cada métrica recebe um veredito (no analysis / healthy / observe /
  needs attention / unhealthy) comparando canary vs. baseline.
- O resultado vira um Risk Score; policies (OPA) e "Failure Strategy"
  transformam o score em ação automática (rollback, ignore, manual).

Conceitos demonstrados:
- Coleta de métricas canary vs. baseline (simulada, sem rede)
- Análise estatística simples (desvio percentual + z-score)
- Risk score agregado por peso de métrica
- Governance gates: AUTO_APPROVE / HOLD / ROLLBACK
"""

import random
import statistics
from dataclasses import dataclass, field
from enum import Enum

random.seed(42)


class Verdict(str, Enum):
    HEALTHY = "✅ HEALTHY"
    OBSERVE = "🟡 OBSERVE"
    UNHEALTHY = "❌ UNHEALTHY"


class GateDecision(str, Enum):
    AUTO_APPROVE = "✅ AUTO-APPROVE"
    HOLD = "⏸️  HOLD (aprovação manual)"
    ROLLBACK = "⛔ ROLLBACK automático"


@dataclass
class MetricSpec:
    """Definição de uma métrica monitorada pelo Continuous Verification."""
    name: str
    weight: float          # peso relativo no risk score
    higher_is_worse: bool  # True p/ erro/latência, False p/ throughput
    warn_pct: float        # desvio % que gera OBSERVE
    fail_pct: float        # desvio % que gera UNHEALTHY


@dataclass
class MetricResult:
    spec: MetricSpec
    baseline: list[float]
    canary: list[float]
    verdict: Verdict = Verdict.HEALTHY
    deviation_pct: float = 0.0
    zscore: float = 0.0

    def evaluate(self) -> None:
        base_mean = statistics.mean(self.baseline)
        canary_mean = statistics.mean(self.canary)
        base_std = statistics.pstdev(self.baseline) or 1e-9

        delta = canary_mean - base_mean
        signed = delta if self.spec.higher_is_worse else -delta
        self.deviation_pct = (signed / base_mean) * 100 if base_mean else 0.0
        self.zscore = signed / base_std

        if self.deviation_pct >= self.spec.fail_pct:
            self.verdict = Verdict.UNHEALTHY
        elif self.deviation_pct >= self.spec.warn_pct:
            self.verdict = Verdict.OBSERVE
        else:
            self.verdict = Verdict.HEALTHY

    def risk_contribution(self) -> float:
        """0 (saudável) .. 100 (crítico) ponderado pelo peso da métrica."""
        raw = {Verdict.HEALTHY: 0, Verdict.OBSERVE: 50, Verdict.UNHEALTHY: 100}[self.verdict]
        return raw * self.spec.weight


# ---------------------------------------------------------------------------
# Health Source: métricas monitoradas (estilo Health Source do Harness)
# ---------------------------------------------------------------------------

METRICS = [
    MetricSpec("error_rate",   weight=0.40, higher_is_worse=True,  warn_pct=20, fail_pct=50),
    MetricSpec("p95_latency",  weight=0.30, higher_is_worse=True,  warn_pct=15, fail_pct=40),
    MetricSpec("apdex",        weight=0.20, higher_is_worse=False, warn_pct=10, fail_pct=25),
    MetricSpec("log_errors",   weight=0.10, higher_is_worse=True,  warn_pct=30, fail_pct=80),
]


def sample(mean: float, jitter: float, n: int = 12) -> list[float]:
    """Gera uma série temporal sintética em torno de uma média."""
    return [max(0.0, random.gauss(mean, jitter)) for _ in range(n)]


@dataclass
class Deployment:
    """Um deploy sob verificação; canary_shift move a média das métricas."""
    name: str
    canary_shift: dict[str, float] = field(default_factory=dict)

    def collect(self) -> list[MetricResult]:
        baselines = {
            "error_rate":  1.0,   # %
            "p95_latency": 240.0, # ms
            "apdex":       0.94,  # 0..1
            "log_errors":  5.0,   # ocorrências/min
        }
        jitter = {"error_rate": 0.15, "p95_latency": 18.0, "apdex": 0.01, "log_errors": 1.0}
        results = []
        for spec in METRICS:
            base = baselines[spec.name]
            baseline = sample(base, jitter[spec.name])
            shift = self.canary_shift.get(spec.name, 1.0)
            canary = sample(base * shift, jitter[spec.name])
            r = MetricResult(spec=spec, baseline=baseline, canary=canary)
            r.evaluate()
            results.append(r)
        return results


# ---------------------------------------------------------------------------
# Governance gate: transforma risk score em decisão
# ---------------------------------------------------------------------------

def apply_governance_gate(risk_score: float, has_unhealthy: bool) -> GateDecision:
    """
    Política de governança (estilo Failure Strategy + OPA policy):
    - risk >= 60 OU qualquer métrica UNHEALTHY → rollback automático
    - 25 <= risk < 60 → segura para aprovação manual
    - risk < 25 → promove automaticamente
    """
    if risk_score >= 60 or has_unhealthy:
        return GateDecision.ROLLBACK
    if risk_score >= 25:
        return GateDecision.HOLD
    return GateDecision.AUTO_APPROVE


def verify_deployment(dep: Deployment) -> None:
    print("\n" + "─" * 70)
    print(f"🚀 Continuous Verification — deploy '{dep.name}'")
    print("─" * 70)
    print("  Coletando 12 data points por métrica (canary vs. baseline)...\n")

    results = dep.collect()
    print(f"  {'Métrica':<14} {'Baseline':>10} {'Canary':>10} {'Desvio':>9} {'z':>6}  Veredito")
    print(f"  {'─'*14} {'─'*10} {'─'*10} {'─'*9} {'─'*6}  {'─'*12}")
    for r in results:
        b = statistics.mean(r.baseline)
        c = statistics.mean(r.canary)
        print(f"  {r.spec.name:<14} {b:>10.2f} {c:>10.2f} "
              f"{r.deviation_pct:>+8.1f}% {r.zscore:>+6.2f}  {r.verdict.value}")

    risk_score = sum(r.risk_contribution() for r in results)
    has_unhealthy = any(r.verdict is Verdict.UNHEALTHY for r in results)
    decision = apply_governance_gate(risk_score, has_unhealthy)

    print(f"\n  🎯 Risk Score agregado: {risk_score:.1f}/100")
    print(f"  🛡️  Governance gate → {decision.value}")

    if decision is GateDecision.ROLLBACK:
        print("     Ação: revertendo para a versão estável anterior. Deploy bloqueado.")
    elif decision is GateDecision.HOLD:
        print("     Ação: pausado. Notificando aprovador via Slack/Jira antes de promover.")
    else:
        print("     Ação: canary saudável — promovendo para 100% do tráfego.")


def run_demo() -> None:
    print("=" * 70)
    print("🔬 Harness Continuous Verification — verificação pós-deploy")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)
    print("""
  O Harness CV coleta métricas de um Health Source durante uma janela
  pós-deploy e compara o canary contra o baseline. Cada métrica recebe
  um veredito; o conjunto vira um Risk Score que a Failure Strategy
  converte em ação automática. Abaixo, três deploys com saúde diferente.""")

    scenarios = [
        Deployment("v3.1.0 — refactor saudável",
                   canary_shift={"error_rate": 1.05, "p95_latency": 1.03,
                                 "apdex": 1.0, "log_errors": 1.1}),
        Deployment("v3.2.0 — regressão de latência",
                   canary_shift={"error_rate": 1.2, "p95_latency": 1.35,
                                 "apdex": 0.9, "log_errors": 1.4}),
        Deployment("v3.3.0 — bug crítico",
                   canary_shift={"error_rate": 2.6, "p95_latency": 1.6,
                                 "apdex": 0.7, "log_errors": 3.0}),
    ]
    for dep in scenarios:
        verify_deployment(dep)

    print("\n" + "=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  A Continuous Verification remove o "olhar humano no dashboard" do
  caminho crítico do deploy: a saúde vira um número (risk score) e a
  política de governança decide sozinha entre promover, segurar ou
  reverter — em segundos, de forma auditável.

  No Vídeo 5.2, vamos ver como o Argo Rollouts faz análise parecida
  dentro do Kubernetes com AnalysisTemplate e Experiment.
    """)


if __name__ == "__main__":
    run_demo()
