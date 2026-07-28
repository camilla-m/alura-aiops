"""
Vídeo 4.2 — Paralelismo dinâmico e cache inteligente
================================================================
A partir de um grafo de dependências entre stages (DAG), calcula o
tempo de execução sequencial e o tempo com paralelismo ótimo (níveis
topológicos + caminho crítico). Em seguida aplica cache inteligente:
stages cujos inputs não mudaram viram cache hit (tempo ~0). Mostra o
ganho de tempo total em cada etapa.

Conceitos demonstrados:
- Modelagem de pipeline como DAG (grafo acíclico direcionado)
- Ordenação topológica em níveis para paralelismo
- Caminho crítico como limite inferior do tempo paralelo
- Cache por hash de inputs (cache hit = tempo zero)
"""

from dataclasses import dataclass, field


@dataclass
class Stage:
    """Um estágio do pipeline com dependências e assinatura de inputs."""
    name: str
    duration: float                       # segundos
    depends_on: list[str] = field(default_factory=list)
    inputs_hash: str = ""                 # hash dos arquivos/inputs do stage


# ---------------------------------------------------------------------------
# Cenário: pipeline com fan-out. lint/unit-test/e2e-test independem entre si.
# ---------------------------------------------------------------------------

PIPELINE = [
    Stage("checkout",  12,  [],                       inputs_hash="src@a1"),
    Stage("build",     180, ["checkout"],             inputs_hash="src@a1"),
    Stage("lint",      45,  ["checkout"],             inputs_hash="src@a1"),
    Stage("unit-test", 420, ["build"],                inputs_hash="src@a1"),
    Stage("e2e-test",  240, ["build"],                inputs_hash="src@a1"),
    Stage("package",   60,  ["unit-test", "e2e-test"], inputs_hash="src@a1"),
    Stage("deploy",    90,  ["package", "lint"],       inputs_hash="cfg@b2"),
]


def topological_levels(stages: list[Stage]) -> list[list[Stage]]:
    """Agrupa stages em níveis: cada nível pode rodar em paralelo."""
    by_name = {s.name: s for s in stages}
    nivel_de: dict[str, int] = {}

    def resolve(nome: str) -> int:
        if nome in nivel_de:
            return nivel_de[nome]
        deps = by_name[nome].depends_on
        n = 0 if not deps else 1 + max(resolve(d) for d in deps)
        nivel_de[nome] = n
        return n

    for s in stages:
        resolve(s.name)

    max_nivel = max(nivel_de.values())
    niveis: list[list[Stage]] = [[] for _ in range(max_nivel + 1)]
    for s in stages:
        niveis[nivel_de[s.name]].append(s)
    return niveis


def critical_path(stages: list[Stage], cached: set[str]) -> tuple[float, list[str]]:
    """Maior caminho de custo acumulado no DAG (cache = custo 0)."""
    by_name = {s.name: s for s in stages}
    memo: dict[str, tuple[float, list[str]]] = {}

    def custo(s: Stage) -> float:
        return 0.0 if s.name in cached else s.duration

    def melhor(nome: str) -> tuple[float, list[str]]:
        if nome in memo:
            return memo[nome]
        s = by_name[nome]
        if not s.depends_on:
            memo[nome] = (custo(s), [nome])
            return memo[nome]
        t_dep, caminho_dep = max((melhor(d) for d in s.depends_on), key=lambda x: x[0])
        memo[nome] = (t_dep + custo(s), caminho_dep + [nome])
        return memo[nome]

    return max((melhor(s.name) for s in stages), key=lambda x: x[0])


def tempo_paralelo(niveis: list[list[Stage]], cached: set[str]) -> float:
    """Soma o stage mais lento de cada nível (paralelismo dentro do nível)."""
    total = 0.0
    for nivel in niveis:
        custos = [0.0 if s.name in cached else s.duration for s in nivel]
        total += max(custos)
    return total


def detectar_cache_hits(stages: list[Stage], baseline: dict[str, str]) -> set[str]:
    """Cache hit quando o hash de inputs bate com o baseline do último run."""
    return {s.name for s in stages if baseline.get(s.name) == s.inputs_hash}


def run() -> None:
    print("=" * 70)
    print("⚡ Paralelismo dinâmico + cache inteligente")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)

    sequencial = sum(s.duration for s in PIPELINE)
    niveis = topological_levels(PIPELINE)

    print("\n  DAG do pipeline (níveis topológicos):\n")
    for i, nivel in enumerate(niveis):
        nomes = ", ".join(f"{s.name}({s.duration:.0f}s)" for s in nivel)
        marca = " ← rodam em paralelo" if len(nivel) > 1 else ""
        print(f"    Nível {i}: {nomes}{marca}")

    # --- 1) Sequencial ---
    print("\n" + "─" * 70)
    print("1️⃣  EXECUÇÃO SEQUENCIAL (um stage por vez)")
    print("─" * 70)
    print(f"    Tempo total: {sequencial:.0f}s ({sequencial/60:.1f} min)")

    # --- 2) Paralelismo ótimo (sem cache) ---
    par = tempo_paralelo(niveis, cached=set())
    t_cp, caminho = critical_path(PIPELINE, cached=set())
    print("\n" + "─" * 70)
    print("2️⃣  PARALELISMO ÓTIMO (níveis topológicos)")
    print("─" * 70)
    print(f"    Tempo total  : {par:.0f}s ({par/60:.1f} min)")
    print(f"    Caminho crít.: {' → '.join(caminho)} = {t_cp:.0f}s")
    print(f"    Ganho vs seq.: -{sequencial - par:.0f}s "
          f"({100*(sequencial-par)/sequencial:.0f}% mais rápido)")

    # --- 3) Paralelismo + cache inteligente ---
    baseline = {s.name: s.inputs_hash for s in PIPELINE}   # último run
    baseline["deploy"] = "cfg@OLD"                          # só o deploy mudou
    cached = detectar_cache_hits(PIPELINE, baseline)
    par_cache = tempo_paralelo(niveis, cached)
    t_cp2, caminho2 = critical_path(PIPELINE, cached)

    print("\n" + "─" * 70)
    print("3️⃣  PARALELISMO + CACHE INTELIGENTE")
    print("─" * 70)
    print(f"    Inputs inalterados desde o último run → cache HIT (custo ~0):")
    print(f"      {', '.join(sorted(cached)) or 'nenhum'}")
    print(f"    Recomputados (input mudou): "
          f"{', '.join(s.name for s in PIPELINE if s.name not in cached)}")
    print(f"    Tempo total  : {par_cache:.0f}s ({par_cache/60:.1f} min)")
    print(f"    Caminho crít.: {' → '.join(caminho2)} = {t_cp2:.0f}s")

    # --- Resumo ---
    print("\n" + "=" * 70)
    print("📊 GANHO ACUMULADO")
    print("=" * 70)
    linhas = [
        ("Sequencial",              sequencial),
        ("+ Paralelismo",           par),
        ("+ Cache inteligente",     par_cache),
    ]
    print()
    for nome, t in linhas:
        eco = sequencial - t
        print(f"  {nome:<24}{t:>6.0f}s ({t/60:4.1f} min)   economia: -{eco:>4.0f}s")

    print(f"\n  ✅ Do início ao fim: {sequencial:.0f}s → {par_cache:.0f}s "
          f"({100*(sequencial-par_cache)/sequencial:.0f}% mais rápido)")

    print("\n" + "=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  O DAG revela quais stages são independentes e podem correr juntos; o
  caminho crítico define o piso do tempo paralelo. O cache elimina
  trabalho repetido quando nada mudou nos inputs.

  No Vídeo 4.3, vamos além: pular stages inteiros com segurança quando
  o diff de mudanças mostra que eles nem precisam rodar.
    """)


if __name__ == "__main__":
    run()
