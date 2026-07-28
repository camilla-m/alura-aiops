"""
Vídeo 3.3 — Flaky tests: detectando instabilidade sem mudança de código
=======================================================================
Analisa o histórico de execuções (pass/fail por run, com commit
associado) e detecta testes flaky: os que falham e passam de forma
intermitente PARA O MESMO commit. Calcula um flakiness score, coloca
os piores em quarentena e ranqueia o que priorizar para fix.

Conceitos demonstrados:
- Histórico de execuções indexado por commit
- Flakiness score = inconsistência intra-commit + transições pass↔fail
- Distinção entre flaky e falha real (falha consistente após mudança)
- Quarentena automática dos testes acima de um limiar
"""

import random
from collections import defaultdict
from dataclasses import dataclass, field

random.seed(42)

QUARANTINE_THRESHOLD = 0.30  # score acima disto → quarentena


@dataclass
class Run:
    """Uma execução de um teste em um commit específico."""
    commit: str
    passed: bool


@dataclass
class TestHistory:
    """Histórico completo de execuções de um teste."""
    name: str
    runs: list[Run] = field(default_factory=list)

    @property
    def total_runs(self) -> int:
        return len(self.runs)

    @property
    def fail_rate(self) -> float:
        if not self.runs:
            return 0.0
        return sum(1 for r in self.runs if not r.passed) / len(self.runs)

    def by_commit(self) -> dict[str, list[bool]]:
        grouped: dict[str, list[bool]] = defaultdict(list)
        for r in self.runs:
            grouped[r.commit].append(r.passed)
        return grouped

    @property
    def inconsistent_commits(self) -> int:
        """Commits em que o teste passou E falhou (a marca do flaky)."""
        return sum(
            1 for results in self.by_commit().values()
            if any(results) and not all(results)
        )

    @property
    def flakiness_score(self) -> float:
        """
        Score em [0, 1]. Combina:
        - 70%: fração de commits com resultado inconsistente (intra-commit)
        - 30%: fração de transições pass↔fail na sequência de runs
        Um teste que sempre falha (fail_rate=1) tem score BAIXO: é falha
        real e consistente, não flakiness.
        """
        commits = self.by_commit()
        if not commits:
            return 0.0

        inconsistency = self.inconsistent_commits / len(commits)

        transitions = sum(
            1 for a, b in zip(self.runs, self.runs[1:]) if a.passed != b.passed
        )
        max_transitions = max(len(self.runs) - 1, 1)
        flip_ratio = transitions / max_transitions

        return round(0.7 * inconsistency + 0.3 * flip_ratio, 3)

    @property
    def is_flaky(self) -> bool:
        return self.flakiness_score >= QUARANTINE_THRESHOLD


# ---------------------------------------------------------------------------
# Geração do histórico simulado
# ---------------------------------------------------------------------------

COMMITS = [f"c{i:03d}" for i in range(12)]


def make_history(name: str, profile: str) -> TestHistory:
    """
    Gera runs conforme um perfil:
    - stable:    passa quase sempre
    - flaky:     ~30% de falha aleatória, independente do commit
    - very_flaky:~50% de falha aleatória (timing/rede)
    - real_fail: verde até um commit; a partir dele falha SEMPRE (bug real)
    """
    runs: list[Run] = []
    broke_at = random.randint(2, 4)  # regressão cedo → falha consistente na maioria
    for idx, commit in enumerate(COMMITS):
        # Cada commit é executado 3x (ex.: retries no CI)
        for _ in range(3):
            if profile == "stable":
                passed = random.random() > 0.02
            elif profile == "flaky":
                passed = random.random() > 0.30
            elif profile == "very_flaky":
                passed = random.random() > 0.50
            elif profile == "real_fail":
                passed = idx < broke_at
            else:
                passed = True
            runs.append(Run(commit=commit, passed=passed))
    return TestHistory(name=name, runs=runs)


def build_dataset() -> list[TestHistory]:
    specs = [
        ("test_auth_login_flow", "stable"),
        ("test_payment_gateway_timeout", "very_flaky"),
        ("test_search_pagination", "flaky"),
        ("test_cart_total_calc", "stable"),
        ("test_email_delivery_async", "very_flaky"),
        ("test_report_export_pdf", "flaky"),
        ("test_user_profile_update", "stable"),
        ("test_inventory_sync", "real_fail"),   # falha REAL, não flaky
    ]
    return [make_history(name, profile) for name, profile in specs]


def classify(h: TestHistory) -> str:
    if h.is_flaky:
        return "🔶 FLAKY"
    # Falha consistente (score baixo mas fail_rate alto) = regressão real.
    if h.fail_rate > 0.5:
        return "❌ FALHA REAL"
    return "✅ ESTÁVEL"


def run_analysis() -> None:
    print("=" * 70)
    print("🔶 Flaky tests: detectando instabilidade sem mudança de código")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)

    dataset = build_dataset()
    total_runs = sum(h.total_runs for h in dataset)
    print(f"\n  Histórico analisado: {len(dataset)} testes, "
          f"{len(COMMITS)} commits, {total_runs} execuções")
    print(f"  Limiar de quarentena: flakiness score ≥ {QUARANTINE_THRESHOLD}")

    ranked = sorted(dataset, key=lambda h: h.flakiness_score, reverse=True)

    # --- Tabela ranqueada ---
    print("\n" + "─" * 70)
    print("📊 RANKING POR FLAKINESS SCORE")
    print("─" * 70)
    print(f"\n  {'Teste':<32}{'Score':>7}{'Fail%':>8}{'Incons.':>9}  Classificação")
    print(f"  {'─'*31:<32}{'─'*6:>7}{'─'*7:>8}{'─'*8:>9}  {'─'*14}")
    for h in ranked:
        print(
            f"  {h.name:<32}{h.flakiness_score:>7.3f}{h.fail_rate*100:>7.0f}%"
            f"{h.inconsistent_commits:>6}/{len(h.by_commit()):<3}"
            f"  {classify(h)}"
        )

    # --- Quarentena ---
    quarantined = [h for h in ranked if h.is_flaky]
    print("\n" + "─" * 70)
    print("🚧 QUARENTENA (não bloqueiam o pipeline até serem corrigidos)")
    print("─" * 70)
    if quarantined:
        for i, h in enumerate(quarantined, 1):
            print(f"  {i}. {h.name}  (score {h.flakiness_score:.3f})")
            print(f"     → falha em {h.inconsistent_commits} commits SEM mudança de código")
    else:
        print("  Nenhum teste acima do limiar. Suíte estável. 🎉")

    # --- Falha real destacada ---
    print("\n" + "─" * 70)
    print("⚠️  ATENÇÃO: falha real ≠ flaky")
    print("─" * 70)
    for h in ranked:
        if h.fail_rate > 0.5 and not h.is_flaky:
            print(f"  {h.name}: falha CONSISTENTE (fail_rate {h.fail_rate:.0%}).")
            print(f"     Score baixo ({h.flakiness_score:.3f}) porque é determinístico:")
            print(f"     provavelmente um bug REAL introduzido por um commit. NÃO quarentenar,")
            print(f"     bloquear e corrigir o código.")

    print("\n" + "=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print(f"""
  {len(quarantined)} teste(s) flaky isolados; a suíte volta a ser confiável.
  O score separa instabilidade (pass/fail no mesmo commit) de falha real
  (fail consistente após uma mudança) — só o primeiro grupo vai à quarentena.

  No vídeo 3.4 vamos além do resultado e olhamos a COBERTURA: quais testes
  são redundantes, onde estão os gaps e quais têm alto valor.
    """)


if __name__ == "__main__":
    run_analysis()
