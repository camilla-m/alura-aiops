"""
Vídeo 4.4 — Agentes que otimizam o próprio pipeline
================================================================
Um "agente" analisa N execuções passadas e PROPÕE melhorias
estruturais: aumentar paralelismo, cachear stage estável, juntar
stages pequenos e sequenciais, e quarentenar steps flaky. Usa
heurísticas explicáveis (sem LLM real — o raciocínio é simulado
passo a passo) e emite uma lista priorizada de recomendações com
impacto estimado em minutos economizados.

Conceitos demonstrados:
- Agente de otimização baseado em heurísticas auditáveis
- Detecção de oportunidades: paralelismo, cache, merge, quarentena
- Priorização por impacto estimado (min economizados)
- Human-in-the-loop: recomendações exigem aprovação humana
"""

import random
import statistics
from dataclasses import dataclass, field
from enum import Enum


class Kind(str, Enum):
    PARALELIZAR = "🔀 PARALELIZAR"
    CACHEAR = "💾 CACHEAR"
    JUNTAR = "🔗 JUNTAR STAGES"
    QUARENTENA = "🧪 QUARENTENA FLAKY"


@dataclass
class StageStats:
    name: str
    depends_on: list[str]
    durations: list[float] = field(default_factory=list)
    input_changed_rate: float = 1.0   # fração de runs em que o input mudou
    fail_rate: float = 0.0            # fração de runs que falharam (flaky)

    @property
    def mean(self) -> float:
        return statistics.mean(self.durations)

    @property
    def cv(self) -> float:
        return statistics.pstdev(self.durations) / self.mean if self.mean else 0.0


@dataclass
class Recommendation:
    kind: Kind
    target: str
    rationale: str          # o "porquê" explicável
    est_savings_s: float    # impacto estimado em segundos


# ---------------------------------------------------------------------------
# Telemetria sintética de 30 runs
# ---------------------------------------------------------------------------

def build_stats(n_runs: int = 30) -> list[StageStats]:
    random.seed(42)
    perfis = [
        # nome, deps, média, cv_alvo, input_changed_rate, fail_rate
        ("checkout",  [],            12,  0.05, 1.00, 0.00),
        ("build",     ["checkout"],  180, 0.10, 0.30, 0.00),
        ("lint",      ["build"],     45,  0.08, 0.90, 0.00),   # depende à toa
        ("unit-test", ["build"],     420, 0.12, 0.90, 0.05),
        ("e2e-test",  ["build"],     240, 0.45, 0.90, 0.30),   # lento e flaky
        ("docs-gen",  ["checkout"],  25,  0.06, 0.10, 0.00),   # input quase nunca muda
        ("deploy",    ["unit-test", "e2e-test"], 90, 0.10, 1.00, 0.00),
    ]
    stats = []
    for nome, deps, media, cv, chg, fail in perfis:
        durs = [max(1.0, random.gauss(media, media * cv)) for _ in range(n_runs)]
        stats.append(StageStats(nome, deps, durs, chg, fail))
    return stats


# ---------------------------------------------------------------------------
# Heurísticas do agente — cada uma retorna zero ou mais recomendações
# ---------------------------------------------------------------------------

def h_parallelism(stats: list[StageStats]) -> list[Recommendation]:
    """Stages que compartilham as MESMAS dependências podem rodar em paralelo."""
    recs = []
    grupos: dict[tuple, list[StageStats]] = {}
    for s in stats:
        grupos.setdefault(tuple(sorted(s.depends_on)), []).append(s)
    for deps, membros in grupos.items():
        if len(membros) > 1 and deps:
            sequencial = sum(m.mean for m in membros)
            paralelo = max(m.mean for m in membros)
            economia = sequencial - paralelo
            if economia > 30:
                nomes = ", ".join(m.name for m in membros)
                recs.append(Recommendation(
                    Kind.PARALELIZAR, nomes,
                    f"dependem só de {list(deps)} e hoje rodam em série "
                    f"({sequencial:.0f}s); em paralelo custariam {paralelo:.0f}s",
                    economia))
    return recs


def h_cache(stats: list[StageStats]) -> list[Recommendation]:
    """Stage cujo input raramente muda é forte candidato a cache."""
    recs = []
    for s in stats:
        if s.input_changed_rate <= 0.35 and s.mean > 20:
            economia = s.mean * (1 - s.input_changed_rate)
            recs.append(Recommendation(
                Kind.CACHEAR, s.name,
                f"input muda em só {s.input_changed_rate:.0%} dos runs; "
                f"cache hit evita ~{economia:.0f}s por run em média",
                economia))
    return recs


def h_merge(stats: list[StageStats]) -> list[Recommendation]:
    """Stage barato encadeado 1:1 pode ser fundido para cortar overhead."""
    recs = []
    OVERHEAD = 8.0   # overhead fixo de agendar um job separado (s)
    by_name = {s.name: s for s in stats}
    dependentes: dict[str, list[str]] = {}
    for s in stats:
        for d in s.depends_on:
            dependentes.setdefault(d, []).append(s.name)
    for s in stats:
        # encadeamento 1:1: um único pai e um único filho, ambos baratos
        if len(s.depends_on) == 1:
            pai = by_name[s.depends_on[0]]
            if dependentes.get(pai.name) == [s.name] and s.mean < 60:
                recs.append(Recommendation(
                    Kind.JUNTAR, f"{pai.name}+{s.name}",
                    f"'{s.name}' é o único filho de '{pai.name}' e é barato; "
                    f"fundir remove ~{OVERHEAD:.0f}s de overhead de job",
                    OVERHEAD))
    return recs


def h_quarantine(stats: list[StageStats]) -> list[Recommendation]:
    """Step flaky (alta taxa de falha + alta variância) vai pra quarentena."""
    recs = []
    for s in stats:
        if s.fail_rate >= 0.20 and s.cv >= 0.30:
            # retries repetem o custo; assumir ~1 retry evitado por flaky run
            economia = s.mean * s.fail_rate
            recs.append(Recommendation(
                Kind.QUARENTENA, s.name,
                f"falha em {s.fail_rate:.0%} dos runs com CV={s.cv:.2f}; "
                f"quarentenar evita ~{economia:.0f}s/run de retries e não bloqueia o merge",
                economia))
    return recs


def analisar_agente(stats: list[StageStats]) -> list[Recommendation]:
    recs: list[Recommendation] = []
    for heuristica in (h_parallelism, h_cache, h_merge, h_quarantine):
        recs.extend(heuristica(stats))
    return sorted(recs, key=lambda r: r.est_savings_s, reverse=True)


def run() -> None:
    print("=" * 70)
    print("🤖 Agente de otimização de pipeline (heurístico e explicável)")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)

    stats = build_stats()
    print(f"\n  Telemetria analisada: {len(stats[0].durations)} runs, "
          f"{len(stats)} stages.")
    print("  Raciocínio do agente, passo a passo:\n")

    recs = analisar_agente(stats)
    for passo, heur in enumerate(
        ["procurar stages paralelizáveis (mesmas dependências)",
         "procurar stages com input estável (cacheáveis)",
         "procurar encadeamentos 1:1 baratos (fundíveis)",
         "procurar steps flaky (quarentenáveis)"], start=1):
        print(f"    {passo}. {heur} ...")

    print("\n" + "─" * 70)
    print("📋 RECOMENDAÇÕES PRIORIZADAS (por impacto estimado)")
    print("─" * 70 + "\n")

    total = 0.0
    for i, r in enumerate(recs, start=1):
        total += r.est_savings_s
        print(f"  #{i}  {r.kind.value}  →  {r.target}")
        print(f"      Porquê : {r.rationale}")
        print(f"      Impacto: ~{r.est_savings_s:.0f}s economizados "
              f"({r.est_savings_s/60:.1f} min)\n")

    print("─" * 70)
    print(f"  💰 Economia potencial somada: ~{total:.0f}s ({total/60:.1f} min) por run")
    print("─" * 70)

    print("\n" + "=" * 70)
    print("⚠️  HUMAN-IN-THE-LOOP")
    print("=" * 70)
    print("""
  O agente NÃO aplica nada sozinho. Cada recomendação é uma proposta com
  justificativa auditável para o time revisar. Paralelizar pode expor uma
  dependência implícita; quarentenar um teste pode esconder um bug real.
  Por isso toda mudança estrutural passa por aprovação humana antes do merge.

  No Vídeo 4.5, vamos aplicar essas recomendações em um pipeline de exemplo
  e medir o resultado before/after de ponta a ponta.
    """)


if __name__ == "__main__":
    run()
