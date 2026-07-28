"""
Vídeo 5.4 — Buildkite Test Analytics: reliability, flaky e slow tests
======================================================================
Reproduz o Buildkite Test Analytics: ingere resultados de testes de
vários builds, calcula a reliability por teste, detecta slow tests e
flaky tests, mostra tendências (p95 de duração, taxa de falha) e emite
um "test health report".

O que é do Buildkite (real):
- O Buildkite Test Analytics é um produto separado do CI: os runners
  enviam os resultados de cada teste (nome, duração, passou/falhou,
  scope/suite, commit) via um collector/uploader.
- Ele agrega essas execuções e calcula reliability por teste, marca
  "flaky" quando o mesmo teste passa e falha sem mudança de código,
  destaca os testes mais lentos (p95) e mostra tendências no tempo.
- O objetivo é priorizar quais testes consertar: os que mais quebram
  a confiabilidade da suíte e os que mais custam tempo de CI.

Conceitos demonstrados:
- Ingestão de TestExecution (nome, build, commit, duração, status)
- Reliability = passes / execuções, agregada por teste
- Detecção de flaky (resultados mistos no MESMO commit)
- Slow tests via p95 da distribuição de durações
- Tendências por build e test health report priorizado
"""

import random
import statistics
from dataclasses import dataclass, field
from enum import Enum

random.seed(42)


class Status(str, Enum):
    PASSED = "passed"
    FAILED = "failed"


@dataclass
class TestExecution:
    """Uma execução de um teste em um build (o que o collector envia)."""
    test: str
    suite: str
    build: int
    commit: str
    duration_ms: float
    status: Status


@dataclass
class TestHealth:
    test: str
    suite: str
    executions: list[TestExecution] = field(default_factory=list)

    @property
    def runs(self) -> int:
        return len(self.executions)

    @property
    def reliability(self) -> float:
        passes = sum(1 for e in self.executions if e.status is Status.PASSED)
        return passes / self.runs * 100 if self.runs else 100.0

    @property
    def p95_ms(self) -> float:
        durations = sorted(e.duration_ms for e in self.executions)
        if not durations:
            return 0.0
        idx = min(len(durations) - 1, int(round(0.95 * (len(durations) - 1))))
        return durations[idx]

    @property
    def is_flaky(self) -> bool:
        """Flaky = mesmo commit produziu resultados diferentes (passou e falhou)."""
        by_commit: dict[str, set[Status]] = {}
        for e in self.executions:
            by_commit.setdefault(e.commit, set()).add(e.status)
        return any(len(s) > 1 for s in by_commit.values())


# ---------------------------------------------------------------------------
# Geração de dados: 40 builds, alguns testes saudáveis, um flaky, um lento
# ---------------------------------------------------------------------------

SUITE = "rspec"
TESTS = {
    "UserSpec#login":            {"base_ms": 120,  "fail_p": 0.00, "flaky": False},
    "UserSpec#signup":           {"base_ms": 90,   "fail_p": 0.02, "flaky": False},
    "CheckoutSpec#pay":          {"base_ms": 340,  "fail_p": 0.00, "flaky": True},   # flaky!
    "SearchSpec#autocomplete":   {"base_ms": 210,  "fail_p": 0.01, "flaky": False},
    "ReportSpec#monthly_export": {"base_ms": 4200, "fail_p": 0.00, "flaky": False},  # slow!
    "AuthSpec#oauth_callback":   {"base_ms": 160,  "fail_p": 0.06, "flaky": False},  # baixa reliab.
}


def ingest() -> list[TestExecution]:
    executions: list[TestExecution] = []
    for build in range(1, 41):
        commit = f"c{build:03d}"
        for name, cfg in TESTS.items():
            duration = max(5.0, random.gauss(cfg["base_ms"], cfg["base_ms"] * 0.12))
            if cfg["flaky"] and random.random() < 0.25:
                # flaky: falha intermitente sem mudança de código
                status = Status.FAILED if random.random() < 0.5 else Status.PASSED
            else:
                status = Status.FAILED if random.random() < cfg["fail_p"] else Status.PASSED
            executions.append(TestExecution(name, SUITE, build, commit, duration, status))
    return executions


def aggregate(executions: list[TestExecution]) -> dict[str, TestHealth]:
    health: dict[str, TestHealth] = {}
    for e in executions:
        h = health.setdefault(e.test, TestHealth(e.test, e.suite))
        h.executions.append(e)
    return health


def run_demo() -> None:
    print("=" * 70)
    print("📊 Buildkite Test Analytics — saúde da suíte de testes")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)

    executions = ingest()
    health = aggregate(executions)
    print(f"\n  Ingeridas {len(executions)} execuções de {len(health)} testes "
          f"em 40 builds da suíte '{SUITE}'.")

    # --- Reliability por teste ---
    print("\n" + "─" * 70)
    print("🎯 Reliability por teste (ordenado do pior para o melhor)")
    print("─" * 70)
    print(f"  {'Teste':<28} {'runs':>5} {'reliab.':>9} {'p95 dur':>10}  flags")
    print(f"  {'─'*28} {'─'*5} {'─'*9} {'─'*10}  {'─'*12}")
    for h in sorted(health.values(), key=lambda x: x.reliability):
        flags = []
        if h.is_flaky:
            flags.append("🌀 flaky")
        print(f"  {h.test:<28} {h.runs:>5} {h.reliability:>8.1f}% "
              f"{h.p95_ms:>8.0f}ms  {' '.join(flags)}")

    # --- Slow tests (p95) ---
    print("\n" + "─" * 70)
    print("🐢 Slow tests — top 3 por p95 de duração")
    print("─" * 70)
    slow = sorted(health.values(), key=lambda x: x.p95_ms, reverse=True)[:3]
    total_p95 = sum(h.p95_ms for h in health.values())
    for h in slow:
        share = h.p95_ms / total_p95 * 100
        print(f"  {h.test:<28} p95={h.p95_ms:>7.0f}ms  ({share:>4.1f}% do tempo p95 da suíte)")

    # --- Flaky tests ---
    print("\n" + "─" * 70)
    print("🌀 Flaky tests — resultados mistos no mesmo commit")
    print("─" * 70)
    flaky = [h for h in health.values() if h.is_flaky]
    if flaky:
        for h in flaky:
            print(f"  {h.test:<28} reliability={h.reliability:.1f}% "
                  f"→ retries mascaram, mas custam tempo e confiança")
    else:
        print("  Nenhum teste flaky detectado. 🎉")

    # --- Tendências por build (taxa de falha) ---
    print("\n" + "─" * 70)
    print("📈 Tendência — taxa de falha da suíte por janela de 10 builds")
    print("─" * 70)
    for lo in range(1, 41, 10):
        hi = lo + 9
        window = [e for e in executions if lo <= e.build <= hi]
        fails = sum(1 for e in window if e.status is Status.FAILED)
        rate = fails / len(window) * 100
        bar = "█" * int(rate * 2)
        print(f"  builds {lo:>2}-{hi:<2}  {rate:>5.1f}%  {bar}")

    # --- Test health report ---
    print("\n" + "=" * 70)
    print("🩺 TEST HEALTH REPORT — priorização")
    print("=" * 70)
    worst = min(health.values(), key=lambda x: x.reliability)
    slowest = max(health.values(), key=lambda x: x.p95_ms)
    print(f"  Menor reliability : {worst.test} ({worst.reliability:.1f}%)")
    print(f"  Mais lento (p95)  : {slowest.test} ({slowest.p95_ms:.0f}ms)")
    print(f"  Flaky a corrigir  : {', '.join(h.test for h in flaky) or 'nenhum'}")
    print("""
  Ação recomendada:
    1. Quarentenar/consertar o teste flaky (mina a confiança em toda a suíte).
    2. Otimizar ou paralelizar o teste mais lento (domina o tempo de CI).
    3. Investigar o teste de menor reliability (falhas reais recorrentes).""")

    print("\n" + "=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  O Buildkite Test Analytics trata os testes como um SISTEMA observável:
  em vez de olhar só "o build passou?", ele mede reliability, flakiness
  e duração ao longo do tempo, dando um mapa claro de onde investir para
  ter um CI rápido e confiável.

  No Vídeo 5.5, juntamos tudo: um scorecard de maturidade e um roadmap
  de adoção de CI/CD inteligente para a sua organização.
    """)


if __name__ == "__main__":
    run_demo()
