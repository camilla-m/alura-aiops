"""
Vídeo 3.1 — O custo invisível de uma suíte de testes que só cresce
==================================================================
Simula uma suíte de testes que cresce release após release e mostra
o custo acumulado: tempo total de CI, feedback loop, minutos de runner
desperdiçados e o impacto na produtividade do time.

Conceitos demonstrados:
- Crescimento composto do nº de testes e do tempo por teste
- Tempo total de CI vs. tempo de feedback loop (com paralelização)
- Minutos de runner desperdiçados por rodar tudo a cada commit
- Como o feedback lento degrada a produtividade (context switch)
"""

import random
from dataclasses import dataclass

random.seed(42)

# Custo de um runner de CI em cloud (valor didático, USD por minuto)
RUNNER_COST_PER_MIN = 0.008
# Nº de runners paralelos disponíveis no pipeline
PARALLEL_RUNNERS = 8
# Commits por dia que disparam a suíte completa
COMMITS_PER_DAY = 40
# Fração de testes de fato relevantes para um commit típico
RELEVANT_FRACTION = 0.06


@dataclass
class ReleaseSnapshot:
    """Estado da suíte de testes em uma release específica."""
    release: str
    num_tests: int
    avg_test_seconds: float

    @property
    def total_ci_seconds(self) -> float:
        """Tempo somado de todos os testes (tempo de CPU gasto)."""
        return self.num_tests * self.avg_test_seconds

    @property
    def feedback_loop_seconds(self) -> float:
        """Tempo que o dev espera, considerando paralelização."""
        return self.total_ci_seconds / PARALLEL_RUNNERS

    @property
    def wasted_seconds_per_run(self) -> float:
        """Tempo gasto em testes sem relação com a mudança."""
        return self.total_ci_seconds * (1 - RELEVANT_FRACTION)

    @property
    def daily_runner_cost(self) -> float:
        """Custo diário de runner rodando a suíte inteira a cada commit."""
        minutes = (self.total_ci_seconds / 60) * COMMITS_PER_DAY
        return minutes * RUNNER_COST_PER_MIN


def simulate_growth() -> list[ReleaseSnapshot]:
    """
    Simula 8 releases. A cada release o time adiciona features (mais
    testes) e a suíte fica mais lenta (setup, fixtures, testes de
    integração pesados vão entrando).
    """
    snapshots: list[ReleaseSnapshot] = []
    num_tests = 200
    avg_seconds = 0.8

    for i in range(8):
        snapshots.append(ReleaseSnapshot(
            release=f"v1.{i}",
            num_tests=num_tests,
            avg_test_seconds=round(avg_seconds, 2),
        ))
        # Crescimento composto: +18% a +35% de testes por release
        num_tests = int(num_tests * random.uniform(1.18, 1.35))
        # Testes ficam ~6% mais lentos em média (integração, I/O)
        avg_seconds *= random.uniform(1.03, 1.09)

    return snapshots


def fmt_minutes(seconds: float) -> str:
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.1f} min"
    return f"{minutes / 60:.1f} h"


def ascii_bar(value: float, max_value: float, width: int = 30) -> str:
    filled = int((value / max_value) * width) if max_value else 0
    return "█" * filled + "░" * (width - filled)


def run_report() -> None:
    print("=" * 70)
    print("💸 O custo invisível de uma suíte de testes que só cresce")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)

    snapshots = simulate_growth()
    first, last = snapshots[0], snapshots[-1]

    # --- Evolução da suíte ---
    print("\n" + "─" * 70)
    print("📈 EVOLUÇÃO DA SUÍTE AO LONGO DAS RELEASES")
    print("─" * 70)
    print(f"\n  {'Release':<9}{'Testes':>8}{'s/teste':>9}{'Feedback':>12}{'Custo/dia':>12}")
    print(f"  {'─'*8:<9}{'─'*7:>8}{'─'*8:>9}{'─'*11:>12}{'─'*11:>12}")
    for s in snapshots:
        print(
            f"  {s.release:<9}{s.num_tests:>8}{s.avg_test_seconds:>9.2f}"
            f"{fmt_minutes(s.feedback_loop_seconds):>12}"
            f"{'$' + format(s.daily_runner_cost, '.2f'):>12}"
        )

    # --- Gráfico do feedback loop ---
    print("\n" + "─" * 70)
    print("⏱️  TEMPO DE FEEDBACK LOOP (espera do dev por commit)")
    print("─" * 70)
    print()
    max_fb = max(s.feedback_loop_seconds for s in snapshots)
    for s in snapshots:
        bar = ascii_bar(s.feedback_loop_seconds, max_fb)
        print(f"  {s.release:<6} {bar} {fmt_minutes(s.feedback_loop_seconds):>8}")

    # --- Desperdício ---
    print("\n" + "─" * 70)
    print("🗑️  MINUTOS DE RUNNER DESPERDIÇADOS (última release, v1.7)")
    print("─" * 70)
    wasted_daily_min = (last.wasted_seconds_per_run / 60) * COMMITS_PER_DAY
    wasted_monthly_cost = wasted_daily_min * RUNNER_COST_PER_MIN * 22
    print(f"\n  Testes relevantes por commit típico: ~{RELEVANT_FRACTION:.0%}")
    print(f"  Logo, {1 - RELEVANT_FRACTION:.0%} de cada execução é desperdício puro.")
    print(f"  Desperdício por dia:  {wasted_daily_min:,.0f} min de runner")
    print(f"  Desperdício por mês:  ${wasted_monthly_cost:,.2f} (22 dias úteis)")

    # --- Produtividade ---
    print("\n" + "─" * 70)
    print("🧠 IMPACTO NA PRODUTIVIDADE")
    print("─" * 70)
    growth = last.feedback_loop_seconds / first.feedback_loop_seconds
    # Feedback acima de ~10 min quase sempre gera context switch
    ctx_switches = COMMITS_PER_DAY if last.feedback_loop_seconds > 600 else 0
    print(f"\n  Feedback loop cresceu {growth:.1f}x de {first.release} para {last.release}")
    print(f"     ({fmt_minutes(first.feedback_loop_seconds)} → {fmt_minutes(last.feedback_loop_seconds)})")
    print(f"  Acima de 10 min o dev troca de tarefa e perde o contexto.")
    print(f"  Estimativa: {ctx_switches} context switches/dia no time inteiro.")

    # --- Resumo ---
    print("\n" + "=" * 70)
    print("📊 RESUMO")
    print("=" * 70)
    print(f"""
  A suíte cresceu {last.num_tests / first.num_tests:.1f}x em nº de testes, mas o custo
  não é linear: tempo por teste também sobe, e rodamos TUDO a cada commit.

  O gargalo não é "temos testes demais" — é rodar testes IRRELEVANTES.
  No próximo vídeo (3.2) vamos usar test selection para rodar apenas o
  subconjunto de testes impactado por cada diff.
    """)


if __name__ == "__main__":
    run_report()
