"""
Vídeo 3.5 — Hands-on: pipeline completo de test intelligence
============================================================
Junta tudo da aula em um pipeline de ponta a ponta:
recebe um diff → test selection → "roda" os selecionados →
filtra flaky com retry → reporta veredito (verde/vermelho) e o
tempo economizado vs. rodar a suíte inteira.

Conceitos demonstrados:
- Orquestração selection + flaky + custo em um fluxo único
- Retry automático de testes flaky antes de reprovar o build
- Veredito determinístico: só falha real derruba o build
- Relatório de economia de tempo vs. "rodar tudo"
"""

import random
from dataclasses import dataclass, field
from enum import Enum

random.seed(42)


class Outcome(str, Enum):
    PASS = "✅ PASS"
    FAIL = "❌ FAIL (bug real)"
    FLAKY = "🔶 FLAKY (recuperado no retry)"
    FLAKY_FAIL = "🚧 FLAKY (esgotou retries → quarentena)"


@dataclass(frozen=True)
class Test:
    name: str
    module: str
    seconds: float
    flaky_rate: float = 0.0   # prob. de falhar por instabilidade
    real_bug: bool = False    # falha determinística (bug de verdade)


# ---------------------------------------------------------------------------
# Suíte e coverage map (versão compacta da aula)
# ---------------------------------------------------------------------------

SUITE: list[Test] = [
    Test("test_auth_login",     "auth",    0.4),
    Test("test_auth_tokens",    "auth",    0.5),
    Test("test_billing_invoice","billing", 1.6),
    Test("test_billing_tax",    "billing", 0.9, flaky_rate=0.40),  # flaky conhecido
    Test("test_catalog_search", "catalog", 0.7),
    Test("test_catalog_product","catalog", 0.6),
    Test("test_cart_checkout",  "cart",    1.9),
    Test("test_cart_refund",    "cart",    1.1, real_bug=True),    # bug real introduzido
    Test("test_shipping_rates", "shipping",0.8),
]

COVERAGE_MAP: dict[str, list[str]] = {
    "src/auth/tokens.py":     ["auth", "billing"],   # tokens usados por billing
    "src/billing/invoice.py": ["billing"],
    "src/catalog/search.py":  ["catalog"],
    "src/cart/checkout.py":   ["cart"],
}

KNOWN_FLAKY = {t.name for t in SUITE if t.flaky_rate > 0}
MAX_RETRIES = 2


@dataclass
class TestResult:
    test: Test
    outcome: Outcome
    attempts: int
    elapsed: float


@dataclass
class PipelineReport:
    diff_files: list[str]
    selected: list[Test]
    results: list[TestResult] = field(default_factory=list)

    @property
    def selected_seconds(self) -> float:
        return sum(r.elapsed for r in self.results)

    @property
    def full_seconds(self) -> float:
        return sum(t.seconds for t in SUITE)

    @property
    def real_failures(self) -> list[TestResult]:
        """Só bug real derruba o build; flaky em quarentena não conta."""
        return [r for r in self.results if r.outcome == Outcome.FAIL]

    @property
    def quarantined(self) -> list[TestResult]:
        return [r for r in self.results if r.outcome == Outcome.FLAKY_FAIL]

    @property
    def is_green(self) -> bool:
        return not self.real_failures


def select_tests(diff_files: list[str]) -> list[Test]:
    """Test selection com safety net (arquivo desconhecido → suíte inteira)."""
    if any(f not in COVERAGE_MAP for f in diff_files):
        return list(SUITE)
    modules: set[str] = set()
    for f in diff_files:
        modules.update(COVERAGE_MAP[f])
    return [t for t in SUITE if t.module in modules]


def execute_test(test: Test) -> TestResult:
    """
    'Roda' um teste.
    - Bug real: falha SEMPRE, retry não ajuda → FAIL (derruba o build).
    - Flaky: falha com prob. flaky_rate; re-executa até MAX_RETRIES.
      Recupera em algum retry → FLAKY (build segue verde). Esgota os
      retries → FLAKY_FAIL (vai para quarentena, NÃO derruba o build).
    - Normal: PASS.
    """
    if test.real_bug:
        return TestResult(test, Outcome.FAIL, 1, round(test.seconds, 2))

    elapsed = 0.0
    for attempt in range(1, MAX_RETRIES + 2):
        elapsed += test.seconds
        passed = random.random() > test.flaky_rate if test.flaky_rate else True
        if passed:
            outcome = Outcome.FLAKY if attempt > 1 else Outcome.PASS
            return TestResult(test, outcome, attempt, round(elapsed, 2))

    # Flaky conhecido que esgotou os retries: quarentena, não bloqueia.
    return TestResult(test, Outcome.FLAKY_FAIL, MAX_RETRIES + 1, round(elapsed, 2))


def run_pipeline(title: str, diff_files: list[str]) -> PipelineReport:
    print("\n" + "─" * 70)
    print(f"🚀 {title}")
    print("─" * 70)
    print("  Diff recebido:")
    for f in diff_files:
        print(f"    • {f}")

    report = PipelineReport(diff_files=diff_files, selected=select_tests(diff_files))

    # 1) Selection
    saved_pct = (1 - len(report.selected) / len(SUITE)) * 100
    print(f"\n  [1/3] Test selection: {len(report.selected)}/{len(SUITE)} testes "
          f"({saved_pct:.0f}% descartados)")

    # 2) Execução + filtro flaky
    print(f"  [2/3] Executando selecionados (retry p/ flaky, máx {MAX_RETRIES})...")
    for t in report.selected:
        report.results.append(execute_test(t))
    for r in report.results:
        tag = " (flaky conhecido)" if r.test.name in KNOWN_FLAKY else ""
        retries = f" após {r.attempts} tentativas" if r.attempts > 1 else ""
        print(f"        {r.outcome.value:<32} {r.test.name}{tag}{retries}")

    # 3) Veredito
    print(f"  [3/3] Veredito do build:")
    if report.quarantined:
        q = ", ".join(r.test.name for r in report.quarantined)
        print(f"        🚧 Em quarentena (não bloqueiam): {q}")
    if report.is_green:
        print(f"        🟢 BUILD VERDE — nenhuma falha real")
    else:
        names = ", ".join(r.test.name for r in report.real_failures)
        print(f"        🔴 BUILD VERMELHO — bug(s) real(is): {names}")

    saved_time = report.full_seconds - report.selected_seconds
    print(f"\n  ⏱️  Tempo: {report.selected_seconds:.1f}s (selecionados) "
          f"vs. {report.full_seconds:.1f}s (tudo) → economia de {saved_time:.1f}s")
    return report


def run_lab() -> None:
    print("=" * 70)
    print("🧪 Hands-on: pipeline completo de test intelligence")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)
    print(f"\n  Suíte: {len(SUITE)} testes | flaky conhecidos: {', '.join(KNOWN_FLAKY)}")

    reports = []

    # Cenário A: diff pequeno em auth (billing entra junto via tokens)
    reports.append(run_pipeline(
        "CENÁRIO A — Fix em src/auth/tokens.py",
        ["src/auth/tokens.py"],
    ))

    # Cenário B: diff em catalog, isolado e verde
    reports.append(run_pipeline(
        "CENÁRIO B — Feature em src/catalog/search.py",
        ["src/catalog/search.py"],
    ))

    # Cenário C: arquivo desconhecido → safety net (roda tudo)
    reports.append(run_pipeline(
        "CENÁRIO C — Arquivo novo src/payments/pix.py (safety net)",
        ["src/payments/pix.py"],
    ))

    # --- Resumo final da aula ---
    print("\n" + "=" * 70)
    print("📊 RESUMO DO PIPELINE (3 cenários)")
    print("=" * 70)
    total_saved = sum(r.full_seconds - r.selected_seconds for r in reports)
    total_full = sum(r.full_seconds for r in reports)
    greens = sum(1 for r in reports if r.is_green)
    recovered = sum(1 for r in reports for x in r.results if x.outcome == Outcome.FLAKY)
    quarantined = sum(len(r.quarantined) for r in reports)
    print(f"\n  Builds verdes: {greens}/{len(reports)}")
    print(f"  Tempo economizado no total: {total_saved:.1f}s de {total_full:.1f}s "
          f"({total_saved/total_full*100:.0f}%)")
    print(f"  Flaky recuperados no retry (build seguiu verde): {recovered}")
    print(f"  Flaky em quarentena (esgotaram retries, não bloquearam): {quarantined}")

    print("\n" + "=" * 70)
    print("📌 FECHAMENTO DA AULA 3")
    print("=" * 70)
    print("""
  Test intelligence não é rodar menos por preguiça — é rodar o que importa
  com confiança: selection corta o irrelevante, o filtro de flaky evita
  falsos vermelhos e a análise de impacto mantém a suíte enxuta e coberta.

  Você fechou a Aula 3. No próximo módulo do Curso 4 seguimos para
  deploy inteligente e automação de rollback guiada por sinais.
    """)


if __name__ == "__main__":
    run_lab()
