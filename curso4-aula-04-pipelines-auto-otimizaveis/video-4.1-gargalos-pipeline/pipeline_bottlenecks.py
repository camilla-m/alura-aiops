"""
Vídeo 4.1 — Identificando gargalos no pipeline
================================================================
Recebe o histórico de execuções de um pipeline de CI/CD com vários
stages e a duração de cada um por run. Identifica o stage gargalo,
calcula o tempo total, a contribuição percentual de cada stage e
destaca o caminho crítico e a variância suspeita.

Conceitos demonstrados:
- Análise de histórico de runs para localizar gargalos
- Contribuição percentual de cada stage no tempo total
- Variância / desvio-padrão como sinal de flakiness
- Percentil p95 como pior caso realista
"""

import random
import statistics
from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    CRITICO = "🔴 CRÍTICO"
    ATENCAO = "🟡 ATENÇÃO"
    OK = "🟢 OK"


@dataclass
class StageHistory:
    """Histórico de durações (em segundos) de um stage ao longo dos runs."""
    name: str
    durations: list[float] = field(default_factory=list)

    @property
    def mean(self) -> float:
        return statistics.mean(self.durations)

    @property
    def stdev(self) -> float:
        return statistics.pstdev(self.durations)

    @property
    def p95(self) -> float:
        ordenado = sorted(self.durations)
        idx = min(len(ordenado) - 1, int(round(0.95 * (len(ordenado) - 1))))
        return ordenado[idx]

    @property
    def cv(self) -> float:
        """Coeficiente de variação — variância normalizada pela média."""
        return self.stdev / self.mean if self.mean else 0.0

    def severity(self, pct: float) -> Severity:
        if pct >= 30 or self.cv >= 0.35:
            return Severity.CRITICO
        if pct >= 15 or self.cv >= 0.20:
            return Severity.ATENCAO
        return Severity.OK


# ---------------------------------------------------------------------------
# Cenário: pipeline de e-commerce com 6 stages, 20 execuções históricas
# ---------------------------------------------------------------------------

# (média_s, desvio_relativo) — o "test" é lento E instável de propósito
STAGE_PROFILE = {
    "checkout":  (12, 0.05),
    "build":     (180, 0.10),
    "lint":      (45, 0.08),
    "unit-test": (420, 0.40),   # gargalo: lento e flaky (retries)
    "e2e-test":  (240, 0.30),
    "deploy":    (90, 0.12),
}


def simulate_history(n_runs: int = 20) -> list[StageHistory]:
    """Gera o histórico sintético de N execuções do pipeline."""
    random.seed(42)
    historico = {nome: StageHistory(nome) for nome in STAGE_PROFILE}
    for _ in range(n_runs):
        for nome, (media, desvio) in STAGE_PROFILE.items():
            dur = max(1.0, random.gauss(media, media * desvio))
            historico[nome].durations.append(round(dur, 1))
    return list(historico.values())


def analisar(historico: list[StageHistory]) -> None:
    """Calcula contribuições e imprime a tabela de gargalos."""
    print("=" * 70)
    print("🔍 Análise de gargalos — histórico de execuções do pipeline")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)

    total_medio = sum(s.mean for s in historico)
    n_runs = len(historico[0].durations)
    print(f"\n  Runs analisados : {n_runs}")
    print(f"  Stages          : {len(historico)}")
    print(f"  Tempo total médio: {total_medio:6.1f}s ({total_medio/60:.1f} min)\n")

    print(f"  {'Stage':<12}{'Média':>8}{'p95':>8}{'CV':>7}{'% total':>9}  Severidade")
    print(f"  {'─'*12}{'─'*8}{'─'*8}{'─'*7}{'─'*9}  {'─'*11}")

    ranking: list[tuple[StageHistory, float]] = []
    for s in sorted(historico, key=lambda x: x.mean, reverse=True):
        pct = 100 * s.mean / total_medio
        ranking.append((s, pct))
        barra = "█" * int(pct / 3)
        print(
            f"  {s.name:<12}{s.mean:>7.1f}s{s.p95:>7.1f}s{s.cv:>7.2f}"
            f"{pct:>8.1f}%  {s.severity(pct).value} {barra}"
        )

    # --- Destaques ---
    gargalo, gargalo_pct = ranking[0]
    mais_instavel = max(historico, key=lambda x: x.cv)

    print("\n" + "─" * 70)
    print("🎯 CAMINHO CRÍTICO E GARGALOS")
    print("─" * 70)
    print(f"\n  🥇 Stage gargalo    : '{gargalo.name}' "
          f"({gargalo_pct:.0f}% do tempo total, {gargalo.mean:.0f}s em média)")
    print(f"  📈 Mais instável    : '{mais_instavel.name}' "
          f"(CV={mais_instavel.cv:.2f}, p95={mais_instavel.p95:.0f}s vs média {mais_instavel.mean:.0f}s)")

    desperdicio = gargalo.p95 - gargalo.mean
    print(f"  ⏳ Cauda longa      : no pior caso, '{gargalo.name}' custa "
          f"+{desperdicio:.0f}s além da média (retries/flakiness)")

    criticos = [s.name for s, pct in ranking if s.severity(pct) == Severity.CRITICO]
    print(f"\n  Stages que merecem otimização: {', '.join(criticos) or 'nenhum'}")

    print("\n" + "=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print(f"""
  Sem medir, o time otimizaria o 'build' (parece pesado), mas o dado mostra
  que '{gargalo.name}' domina o tempo total E carrega a maior variância.
  Atacar o gargalo real rende muito mais que micro-otimizações no resto.

  No Vídeo 4.2, vamos modelar as dependências entre stages como um DAG
  e usar paralelismo e cache para reduzir esse tempo total.
    """)


if __name__ == "__main__":
    analisar(simulate_history())
