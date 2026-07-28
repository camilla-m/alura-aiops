"""
Vídeo 3.4 — Test impact analysis: redundância, gaps e testes de alto valor
==========================================================================
A partir de um coverage map (teste → linhas/funcionalidades cobertas),
identifica testes redundantes (cobrem o que outro já cobre), gaps de
cobertura (código sem teste) e testes de alto valor (muita cobertura
única). Sugere uma consolidação enxuta da suíte.

Conceitos demonstrados:
- Cobertura modelada como conjunto de linhas por teste
- Redundância = subconjunto da cobertura de outro teste
- Cobertura única = linhas exclusivas de um teste
- Score de valor (cobertura única + peso de área crítica) por custo
"""

from dataclasses import dataclass


@dataclass
class TestCoverage:
    """Teste com o conjunto de linhas de código que ele exercita."""
    name: str
    lines: set[str]
    seconds: float


# Universo de linhas "cobríveis" do código (id de linha/funcionalidade).
# Linhas 'crit_*' são áreas críticas (pagamento, auth) e valem mais.
ALL_LINES: set[str] = {
    "crit_auth_1", "crit_auth_2", "crit_pay_1", "crit_pay_2", "crit_pay_3",
    "cart_1", "cart_2", "cart_3", "catalog_1", "catalog_2", "catalog_3",
    "ship_1", "ship_2", "report_1", "report_2", "report_3", "report_4",
}
CRITICAL_LINES = {ln for ln in ALL_LINES if ln.startswith("crit_")}


def build_coverage() -> list[TestCoverage]:
    return [
        TestCoverage("test_auth_full",      {"crit_auth_1", "crit_auth_2", "cart_1"}, 1.2),
        TestCoverage("test_auth_smoke",     {"crit_auth_1"}, 0.3),               # redundante
        TestCoverage("test_payment_flow",   {"crit_pay_1", "crit_pay_2", "crit_pay_3"}, 2.1),
        TestCoverage("test_payment_smoke",  {"crit_pay_1", "crit_pay_2"}, 0.4),  # redundante
        TestCoverage("test_cart_ops",       {"cart_1", "cart_2", "cart_3"}, 0.9),
        TestCoverage("test_catalog_search", {"catalog_1", "catalog_2"}, 0.7),
        TestCoverage("test_catalog_extra",  {"catalog_1"}, 0.2),                 # redundante
        TestCoverage("test_shipping",       {"ship_1", "ship_2"}, 0.6),
        TestCoverage("test_reports_slow",   {"report_1", "report_2", "report_3", "report_4"}, 4.8),
    ]
    # Obs: 'catalog_3' e nada de 'report_*' fora de test_reports_slow → gaps abaixo


def find_redundant(suite: list[TestCoverage]) -> dict[str, str]:
    """
    Um teste é redundante se sua cobertura é subconjunto (próprio ou igual)
    da de outro teste distinto. Retorna {teste_redundante: coberto_por}.
    """
    redundant: dict[str, str] = {}
    for t in suite:
        for other in suite:
            if t is other:
                continue
            if t.lines and t.lines <= other.lines and t.name not in redundant:
                # empate de cobertura idêntica: mantém o mais barato
                if t.lines == other.lines and t.seconds <= other.seconds:
                    continue
                redundant[t.name] = other.name
                break
    return redundant


def unique_coverage(test: TestCoverage, suite: list[TestCoverage]) -> set[str]:
    """Linhas cobertas SÓ por este teste (perdidas se ele for removido)."""
    others: set[str] = set()
    for t in suite:
        if t is not test:
            others |= t.lines
    return test.lines - others


def value_score(test: TestCoverage, suite: list[TestCoverage]) -> float:
    """
    Valor = (cobertura única, com peso 3x para linhas críticas) / custo.
    Recompensa testes que protegem áreas críticas de forma barata.
    """
    uniq = unique_coverage(test, suite)
    weighted = sum(3 if ln in CRITICAL_LINES else 1 for ln in uniq)
    return round(weighted / max(test.seconds, 0.1), 2)


def run_analysis() -> None:
    print("=" * 70)
    print("🧬 Test impact analysis: redundância, gaps e alto valor")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)

    suite = build_coverage()
    covered = set().union(*(t.lines for t in suite))
    coverage_pct = len(covered) / len(ALL_LINES) * 100

    print(f"\n  Suíte: {len(suite)} testes cobrindo {len(covered)}/{len(ALL_LINES)} "
          f"linhas ({coverage_pct:.0f}%)")
    print(f"  Tempo total: {sum(t.seconds for t in suite):.1f}s")

    # --- Redundância ---
    redundant = find_redundant(suite)
    print("\n" + "─" * 70)
    print("♻️  TESTES REDUNDANTES (cobertura é subconjunto de outro)")
    print("─" * 70)
    if redundant:
        for name, covered_by in redundant.items():
            t = next(x for x in suite if x.name == name)
            print(f"  {name}  ⊆  {covered_by}   (economiza {t.seconds:.1f}s se removido)")
    else:
        print("  Nenhum teste redundante.")

    # --- Gaps ---
    gaps = ALL_LINES - covered
    print("\n" + "─" * 70)
    print("🕳️  GAPS DE COBERTURA (código sem nenhum teste)")
    print("─" * 70)
    if gaps:
        for ln in sorted(gaps):
            flag = " 🔴 CRÍTICO" if ln in CRITICAL_LINES else ""
            print(f"  • {ln}{flag}")
        print(f"\n  → {len(gaps)} linha(s) sem teste. Priorizar cobrir as críticas.")
    else:
        print("  Cobertura total. 🎉")

    # --- Alto valor ---
    print("\n" + "─" * 70)
    print("⭐ TESTES DE ALTO VALOR (cobertura única / custo)")
    print("─" * 70)
    ranked = sorted(suite, key=lambda t: value_score(t, suite), reverse=True)
    print(f"\n  {'Teste':<22}{'Valor':>7}{'Única':>8}{'Tempo':>9}")
    print(f"  {'─'*21:<22}{'─'*6:>7}{'─'*7:>8}{'─'*8:>9}")
    for t in ranked:
        uniq = unique_coverage(t, suite)
        print(f"  {t.name:<22}{value_score(t, suite):>7.2f}"
              f"{len(uniq):>8}{t.seconds:>8.1f}s")

    # --- Consolidação sugerida ---
    print("\n" + "─" * 70)
    print("✂️  CONSOLIDAÇÃO SUGERIDA")
    print("─" * 70)
    consolidated = [t for t in suite if t.name not in redundant]
    new_covered = set().union(*(t.lines for t in consolidated))
    saved_time = sum(t.seconds for t in suite) - sum(t.seconds for t in consolidated)
    print(f"\n  Remover {len(redundant)} redundante(s): "
          f"{len(suite)} → {len(consolidated)} testes")
    print(f"  Tempo: {sum(t.seconds for t in suite):.1f}s → "
          f"{sum(t.seconds for t in consolidated):.1f}s  (−{saved_time:.1f}s)")
    kept = new_covered == covered
    print(f"  Cobertura preservada: {'✅ sim' if kept else '❌ NÃO'} "
          f"({len(new_covered)}/{len(covered)} linhas mantidas)")

    print("\n" + "=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  A análise de impacto enxuga a suíte sem perder cobertura: remove o que é
  subconjunto de outro, expõe gaps (sobretudo em áreas críticas) e destaca
  os testes que mais protegem por menos tempo.

  No vídeo 3.5 juntamos tudo — selection + flaky + impacto — em um pipeline
  de test intelligence de ponta a ponta.
    """)


if __name__ == "__main__":
    run_analysis()
