"""
Vídeo 3.2 — Test selection: rodando só os testes impactados pelo diff
=====================================================================
Mantém um coverage map (arquivo de código → testes que o cobrem) e,
dado um diff (lista de arquivos alterados), seleciona apenas o
subconjunto de testes relevantes. Compara "rodar tudo" vs. "test
selection" em nº de testes e tempo, validando que nada foi perdido.

Conceitos demonstrados:
- Coverage map como grafo código → testes
- Seleção de testes por arquivos alterados no diff
- Safety net: arquivos sem mapeamento forçam a suíte completa
- Cálculo de economia (nº de testes e tempo de CI)
"""

import random
from dataclasses import dataclass, field

random.seed(42)


@dataclass(frozen=True)
class Test:
    """Um teste com nome e tempo de execução conhecido."""
    name: str
    seconds: float


# ---------------------------------------------------------------------------
# Suíte simulada: 5 módulos, cada um com seus testes
# ---------------------------------------------------------------------------

def build_suite() -> list[Test]:
    """Gera uma suíte com nomes e tempos realistas por módulo."""
    modules = {
        "auth": 14, "billing": 11, "catalog": 9, "cart": 8, "shipping": 6,
    }
    suite: list[Test] = []
    for mod, count in modules.items():
        for i in range(count):
            kind = random.choice(["unit", "unit", "unit", "integration"])
            base = 0.15 if kind == "unit" else 1.6
            suite.append(Test(
                name=f"test_{mod}_{kind}_{i:02d}",
                seconds=round(base * random.uniform(0.7, 1.5), 2),
            ))
    return suite


# coverage_map: arquivo de código → conjunto de prefixos de teste que o exercitam.
# Na vida real isto vem de dados de cobertura (coverage.py, jacoco...).
COVERAGE_MAP: dict[str, list[str]] = {
    "src/auth/login.py":        ["test_auth"],
    "src/auth/tokens.py":       ["test_auth", "test_billing"],  # billing usa tokens
    "src/billing/invoice.py":   ["test_billing"],
    "src/billing/tax.py":       ["test_billing", "test_shipping"],
    "src/catalog/search.py":    ["test_catalog"],
    "src/catalog/product.py":   ["test_catalog", "test_cart"],
    "src/cart/checkout.py":     ["test_cart"],
    "src/shipping/rates.py":    ["test_shipping"],
    "src/shared/utils.py":      ["test_auth", "test_billing", "test_catalog",
                                 "test_cart", "test_shipping"],  # utilitário central
}


@dataclass
class SelectionResult:
    selected: list[Test]
    reason: str
    unmapped_files: list[str] = field(default_factory=list)


def select_tests(diff_files: list[str], suite: list[Test]) -> SelectionResult:
    """
    Seleciona os testes impactados por um diff.

    Regra de segurança: se algum arquivo alterado não está no coverage
    map (arquivo novo ou desconhecido), não sabemos o que ele afeta,
    então caímos para a suíte completa. Nunca arriscamos falso negativo.
    """
    unmapped = [f for f in diff_files if f not in COVERAGE_MAP]
    if unmapped:
        return SelectionResult(
            selected=list(suite),
            reason="arquivo(s) sem mapeamento → suíte completa (safety net)",
            unmapped_files=unmapped,
        )

    prefixes: set[str] = set()
    for f in diff_files:
        prefixes.update(COVERAGE_MAP[f])

    selected = [t for t in suite if any(t.name.startswith(p) for p in prefixes)]
    return SelectionResult(
        selected=selected,
        reason=f"testes ligados a {len(prefixes)} módulo(s): {', '.join(sorted(prefixes))}",
    )


def total_seconds(tests: list[Test]) -> float:
    return sum(t.seconds for t in tests)


def print_diff_case(title: str, diff_files: list[str], suite: list[Test]) -> None:
    print("\n" + "─" * 70)
    print(f"🔀 {title}")
    print("─" * 70)
    print("  Arquivos alterados no diff:")
    for f in diff_files:
        print(f"    • {f}")

    result = select_tests(diff_files, suite)
    full_n, sel_n = len(suite), len(result.selected)
    full_t, sel_t = total_seconds(suite), total_seconds(result.selected)

    saved_tests = (1 - sel_n / full_n) * 100 if full_n else 0
    saved_time = (1 - sel_t / full_t) * 100 if full_t else 0

    print(f"\n  Motivo da seleção: {result.reason}")
    if result.unmapped_files:
        print(f"  ⚠️  Sem mapeamento: {', '.join(result.unmapped_files)}")

    print(f"\n  {'Estratégia':<22}{'Testes':>10}{'Tempo':>12}")
    print(f"  {'─'*21:<22}{'─'*9:>10}{'─'*11:>12}")
    print(f"  {'Rodar tudo':<22}{full_n:>10}{full_t:>10.1f}s")
    print(f"  {'Test selection':<22}{sel_n:>10}{sel_t:>10.1f}s")
    print(f"\n  💰 Economia: {saved_tests:.0f}% menos testes, {saved_time:.0f}% menos tempo")

    # Validação de segurança: nenhum teste relevante pode ficar de fora.
    relevant = relevant_tests_ground_truth(diff_files, suite)
    missed = [t.name for t in relevant if t not in result.selected]
    if missed:
        print(f"  ❌ FALHA: {len(missed)} teste(s) relevante(s) perdido(s)!")
    else:
        print(f"  ✅ Validação: nenhum teste relevante ({len(relevant)}) foi perdido")


def relevant_tests_ground_truth(diff_files: list[str], suite: list[Test]) -> list[Test]:
    """
    'Verdade de campo': o conjunto de testes que DEVERIA rodar para os
    arquivos do diff, derivado direto do coverage map. Usado só para
    validar que a seleção não gera falso negativo.
    """
    prefixes: set[str] = set()
    for f in diff_files:
        prefixes.update(COVERAGE_MAP.get(f, []))
    if any(f not in COVERAGE_MAP for f in diff_files):
        return list(suite)  # desconhecido → tudo é relevante
    return [t for t in suite if any(t.name.startswith(p) for p in prefixes)]


def run_demo() -> None:
    print("=" * 70)
    print("🎯 Test selection: rodando só os testes impactados pelo diff")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)

    suite = build_suite()
    print(f"\n  Suíte completa: {len(suite)} testes, {total_seconds(suite):.1f}s no total")
    print(f"  Coverage map: {len(COVERAGE_MAP)} arquivos de código mapeados")

    # Caso 1: mudança pontual em um módulo isolado
    print_diff_case(
        "CASO 1 — Fix pontual no login",
        ["src/auth/login.py"],
        suite,
    )

    # Caso 2: mudança que atravessa módulos via dependência compartilhada
    print_diff_case(
        "CASO 2 — Alteração em tokens (usado por auth e billing)",
        ["src/auth/tokens.py", "src/billing/invoice.py"],
        suite,
    )

    # Caso 3: mexeu no utilitário central → quase tudo é relevante
    print_diff_case(
        "CASO 3 — Refactor em src/shared/utils.py (usado por todos)",
        ["src/shared/utils.py"],
        suite,
    )

    # Caso 4: arquivo novo, sem histórico de cobertura → safety net
    print_diff_case(
        "CASO 4 — Arquivo novo sem mapeamento (safety net)",
        ["src/payments/pix.py"],
        suite,
    )

    print("\n" + "=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  Test selection troca "rodar tudo por precaução" por "rodar o que o diff
  realmente toca", com uma rede de segurança para o desconhecido.

  Mas há um risco: um teste selecionado pode falhar por instabilidade, não
  por bug real. No vídeo 3.3 vamos detectar esses flaky tests.
    """)


if __name__ == "__main__":
    run_demo()
