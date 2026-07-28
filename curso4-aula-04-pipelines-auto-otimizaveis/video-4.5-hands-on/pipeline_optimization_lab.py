"""
Vídeo 4.5 — Hands-on: Otimizando um pipeline de ponta a ponta
================================================================
Pega um pipeline de exemplo (definido como estrutura de dados), roda
a análise de gargalos, aplica o otimizador de paralelismo + cache e o
skip seguro por diff, e imprime um relatório before/after com o tempo
total e os minutos economizados em cada etapa. Fecha a Aula 4.

Conceitos demonstrados:
- Pipeline declarado como dado (stages, dependências, inputs)
- Funil de otimização: gargalos → paralelismo → cache → skip
- Relatório before/after com minutos economizados por etapa
- Otimização contínua guiada por evidência (não por palpite)
"""

from dataclasses import dataclass, field


@dataclass
class Stage:
    name: str
    duration: float                       # segundos
    depends_on: list[str] = field(default_factory=list)
    inputs: str = "src"                   # rótulo lógico do grupo de inputs
    impact: set[str] = field(default_factory=set)  # categorias que o afetam


# ---------------------------------------------------------------------------
# Pipeline de exemplo (equivalente a um .yml de CI declarativo)
# ---------------------------------------------------------------------------

def build_pipeline() -> list[Stage]:
    return [
        Stage("checkout",  12,  [],                     "src", {"code", "docs", "infra"}),
        Stage("build",     180, ["checkout"],           "src", {"code", "infra"}),
        Stage("lint",      45,  ["checkout"],           "src", {"code"}),
        Stage("unit-test", 420, ["build"],              "src", {"code"}),
        Stage("e2e-test",  240, ["build"],              "src", {"code", "infra"}),
        Stage("docs-site", 30,  ["checkout"],           "docs", {"docs"}),
        Stage("package",   60,  ["unit-test", "e2e-test"], "src", {"code", "infra"}),
        Stage("deploy",    90,  ["package"],            "cfg", {"code", "infra"}),
    ]


def topo_levels(stages: list[Stage]) -> list[list[Stage]]:
    by_name = {s.name: s for s in stages}
    nivel: dict[str, int] = {}

    def resolve(nome: str) -> int:
        if nome in nivel:
            return nivel[nome]
        deps = by_name[nome].depends_on
        nivel[nome] = 0 if not deps else 1 + max(resolve(d) for d in deps)
        return nivel[nome]

    for s in stages:
        resolve(s.name)
    niveis: list[list[Stage]] = [[] for _ in range(max(nivel.values()) + 1)]
    for s in stages:
        niveis[nivel[s.name]].append(s)
    return niveis


def parallel_time(stages: list[Stage], skipped: set[str], cached: set[str]) -> float:
    """Tempo com paralelismo topológico; skip e cache custam 0."""
    total = 0.0
    for nivel in topo_levels(stages):
        custos = [0.0 if (s.name in skipped or s.name in cached) else s.duration
                  for s in nivel]
        total += max(custos) if custos else 0.0
    return total


def sequential_time(stages: list[Stage], skipped: set[str], cached: set[str]) -> float:
    return sum(0.0 if (s.name in skipped or s.name in cached) else s.duration
               for s in stages)


def detect_cache(stages: list[Stage], changed_inputs: set[str]) -> set[str]:
    """Cache hit para stages cujo grupo de inputs não mudou."""
    return {s.name for s in stages if s.inputs not in changed_inputs}


def decide_skips(stages: list[Stage], diff_categories: set[str]) -> set[str]:
    """Skip seguro: stage sem interseção com as categorias do diff."""
    if "desconhecido" in diff_categories:
        return set()   # fail-safe
    return {s.name for s in stages if not (s.impact & diff_categories)}


def linha_relatorio(rotulo: str, tempo: float, base: float) -> None:
    economia = base - tempo
    pct = 100 * economia / base if base else 0
    barra = "█" * int(tempo / base * 30) if base else ""
    print(f"  {rotulo:<28}{tempo:>6.0f}s ({tempo/60:4.1f} min)  "
          f"-{economia:>4.0f}s ({pct:>2.0f}%)  {barra}")


def run() -> None:
    print("=" * 70)
    print("🧪 Hands-on: otimizando um pipeline de ponta a ponta")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)

    pipeline = build_pipeline()

    # Cenário do PR sendo avaliado
    diff_categories = {"code"}            # PR mexeu só em código de aplicação
    changed_inputs = {"src"}             # só o grupo 'src' mudou (docs/cfg estáveis)

    print("\n  Pipeline de exemplo (8 stages):")
    for s in pipeline:
        deps = ", ".join(s.depends_on) or "—"
        print(f"    • {s.name:<11}{s.duration:>4.0f}s   depende de: {deps}")

    print(f"\n  Contexto deste run:")
    print(f"    Categorias do diff : {', '.join(sorted(diff_categories))}")
    print(f"    Inputs alterados   : {', '.join(sorted(changed_inputs))}")

    # --- BEFORE ---
    base = sequential_time(pipeline, set(), set())

    # --- Etapa a etapa ---
    t_par = parallel_time(pipeline, set(), set())

    cached = detect_cache(pipeline, changed_inputs)
    t_cache = parallel_time(pipeline, set(), cached)

    skipped = decide_skips(pipeline, diff_categories)
    # não faz sentido "pular" algo que já é cache hit; unir os conjuntos
    t_final = parallel_time(pipeline, skipped, cached)

    print("\n" + "─" * 70)
    print("📊 RELATÓRIO BEFORE / AFTER")
    print("─" * 70 + "\n")
    linha_relatorio("BEFORE (sequencial)",      base,    base)
    linha_relatorio("+ Paralelismo (DAG)",      t_par,   base)
    linha_relatorio("+ Cache inteligente",      t_cache, base)
    linha_relatorio("+ Skip seguro por diff",   t_final, base)

    print("\n" + "─" * 70)
    print("🔎 O que a otimização decidiu")
    print("─" * 70)
    print(f"  Cache HIT (input estável): {', '.join(sorted(cached)) or 'nenhum'}")
    print(f"  Skip seguro (diff só code): {', '.join(sorted(skipped)) or 'nenhum'}")
    rodam = [s.name for s in pipeline if s.name not in cached and s.name not in skipped]
    print(f"  Ainda executam            : {', '.join(rodam)}")

    economia = base - t_final
    print("\n" + "=" * 70)
    print("🏁 RESULTADO FINAL")
    print("=" * 70)
    print(f"\n  Tempo total: {base:.0f}s → {t_final:.0f}s")
    print(f"  Economia   : {economia:.0f}s ({economia/60:.1f} min) por run "
          f"— {100*economia/base:.0f}% mais rápido")
    print(f"  Em 50 runs/dia: ~{economia*50/3600:.1f} horas de CI economizadas por dia")

    print("\n" + "=" * 70)
    print("📌 FECHAMENTO DA AULA 4")
    print("=" * 70)
    print("""
  Um pipeline auto-otimizável não é mágica: é medir gargalos, modelar
  dependências, cachear o que não mudou e pular com segurança o que não
  importa — sempre com o humano aprovando as mudanças estruturais.

  Você viu o ciclo completo: da análise de histórico (4.1) ao agente de
  recomendações (4.4), fechando aqui com um resultado before/after real.
  Na próxima aula, levamos essa inteligência para a decisão de deploy.
    """)


if __name__ == "__main__":
    run()
