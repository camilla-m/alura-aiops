"""
Vídeo 2.2 — Canary analysis: decidir promover ou reverter com estatística
==========================================================================
Compara as métricas do baseline (versão stable) com as do canary
(versão nova) e decide PROMOTE / ROLLBACK / INCONCLUSIVE. A decisão
NÃO é "o canary parece pior?", e sim "a diferença é estatisticamente
significativa?" — para não reverter por causa de ruído.

Conceitos demonstrados:
- Comparar baseline vs canary em error_rate e latência p95
- z-test de proporção para taxa de erro (uma cauda: canary pior?)
- Mann-Whitney U para latência (não assume distribuição normal)
- Decisão por p-value + significância (alpha) em vez de "achismo"

Obs.: usa scipy.stats quando disponível; caso contrário cai em uma
implementação equivalente em stdlib, para rodar em qualquer ambiente.
"""

import math
import random
from dataclasses import dataclass
from enum import Enum

try:  # scipy é o ferramental de produção; o fallback mantém tudo executável
    from scipy import stats as _scipy_stats
except ImportError:  # pragma: no cover
    _scipy_stats = None

random.seed(42)

ALPHA = 0.05  # nível de significância: risco de reverter à toa (falso positivo)


class Veredito(str, Enum):
    PROMOTE = "✅ PROMOTE"
    ROLLBACK = "❌ ROLLBACK"
    INCONCLUSIVE = "🤔 INCONCLUSIVE"


@dataclass
class Amostra:
    """Telemetria coletada de um grupo (baseline ou canary)."""
    nome: str
    erros: int
    total: int
    latencias_ms: list[float]

    @property
    def error_rate(self) -> float:
        return self.erros / self.total if self.total else 0.0

    @property
    def p95(self) -> float:
        return percentil(self.latencias_ms, 95)


def percentil(valores: list[float], p: float) -> float:
    if not valores:
        return 0.0
    ordenados = sorted(valores)
    k = (len(ordenados) - 1) * (p / 100)
    baixo, alto = math.floor(k), math.ceil(k)
    if baixo == alto:
        return ordenados[int(k)]
    return ordenados[baixo] + (ordenados[alto] - ordenados[baixo]) * (k - baixo)


def _phi(z: float) -> float:
    """CDF da normal padrão via função erro (stdlib)."""
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def ztest_proporcao(a: Amostra, b: Amostra) -> tuple[float, float]:
    """
    z-test de duas proporções, uma cauda (H1: erro do canary > baseline).
    Retorna (estatística z, p-value). p pequeno => aumento real de erro.
    """
    p1, n1 = a.error_rate, a.total
    p2, n2 = b.error_rate, b.total
    p_pool = (a.erros + b.erros) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return 0.0, 1.0
    z = (p2 - p1) / se
    return z, 1 - _phi(z)  # cauda superior: canary pior


def mann_whitney(baseline: list[float], canary: list[float]) -> tuple[float, float]:
    """
    Mann-Whitney U, uma cauda (H1: latências do canary > baseline).
    Usa scipy quando disponível; senão, aproximação normal do rank-sum.
    """
    if _scipy_stats is not None:
        u, p = _scipy_stats.mannwhitneyu(canary, baseline, alternative="greater")
        return float(u), float(p)

    # Fallback stdlib: soma de ranks + aproximação normal
    n1, n2 = len(canary), len(baseline)
    marcados = [(v, "c") for v in canary] + [(v, "b") for v in baseline]
    marcados.sort(key=lambda x: x[0])
    soma_ranks_c = 0.0
    i = 0
    while i < len(marcados):
        j = i
        while j + 1 < len(marcados) and marcados[j + 1][0] == marcados[i][0]:
            j += 1
        rank_medio = (i + j) / 2 + 1  # ranks começam em 1
        soma_ranks_c += sum(rank_medio for _, g in marcados[i:j + 1] if g == "c")
        i = j + 1
    u_c = soma_ranks_c - n1 * (n1 + 1) / 2
    mu = n1 * n2 / 2
    sigma = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    z = (u_c - mu) / sigma if sigma else 0.0
    return u_c, 1 - _phi(z)


# ---------------------------------------------------------------------------
# Geração de telemetria sintética para dois cenários
# ---------------------------------------------------------------------------

def gerar_amostra(nome: str, n: int, taxa_erro: float, lat_media: float,
                  lat_sigma: float) -> Amostra:
    erros = sum(1 for _ in range(n) if random.random() < taxa_erro)
    latencias = [max(1.0, random.lognormvariate(math.log(lat_media), lat_sigma))
                 for _ in range(n)]
    return Amostra(nome, erros, n, latencias)


def decidir(baseline: Amostra, canary: Amostra) -> tuple[Veredito, dict]:
    z, p_erro = ztest_proporcao(baseline, canary)
    _, p_lat = mann_whitney(baseline.latencias_ms, canary.latencias_ms)

    erro_pior = canary.error_rate > baseline.error_rate and p_erro < ALPHA
    lat_pior = canary.p95 > baseline.p95 and p_lat < ALPHA

    if erro_pior or lat_pior:
        veredito = Veredito.ROLLBACK
    elif min(baseline.total, canary.total) < 200:
        veredito = Veredito.INCONCLUSIVE  # amostra pequena, pouco poder
    else:
        veredito = Veredito.PROMOTE

    return veredito, {"z": z, "p_erro": p_erro, "p_lat": p_lat,
                      "erro_pior": erro_pior, "lat_pior": lat_pior}


def relatar(baseline: Amostra, canary: Amostra) -> None:
    veredito, r = decidir(baseline, canary)
    print(f"\n{'─' * 70}")
    print(f"  Métrica              {'baseline':>12} {'canary':>12}   {'p-value':>9}")
    print(f"{'─' * 70}")
    print(f"  error_rate         {baseline.error_rate*100:>10.2f}% "
          f"{canary.error_rate*100:>11.2f}%   {r['p_erro']:>9.4f}"
          f"  {'⚠️' if r['erro_pior'] else 'ok'}")
    print(f"  latência p95 (ms)  {baseline.p95:>11.0f} {canary.p95:>12.0f}   "
          f"{r['p_lat']:>9.4f}  {'⚠️' if r['lat_pior'] else 'ok'}")
    print(f"\n  Amostras: baseline n={baseline.total}, canary n={canary.total} "
          f"| alpha={ALPHA}")
    print(f"  Racional:")
    print(f"    - erro do canary é estatisticamente maior? "
          f"{'SIM' if r['erro_pior'] else 'não'} (p={r['p_erro']:.4f})")
    print(f"    - latência p95 do canary é maior?          "
          f"{'SIM' if r['lat_pior'] else 'não'} (p={r['p_lat']:.4f})")
    print(f"\n  🧮 VEREDITO: {veredito.value}")


def executar() -> None:
    engine = "scipy.stats" if _scipy_stats is not None else "fallback stdlib"
    print("=" * 70)
    print("🔬 Canary analysis: promover ou reverter, com significância")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)
    print(f"\n  Motor estatístico: {engine}")
    print("  Testes: z-test de proporção (erro) + Mann-Whitney U (latência p95)")

    baseline = gerar_amostra("stable", 1200, taxa_erro=0.010, lat_media=120, lat_sigma=0.35)

    print("\n" + "=" * 70)
    print("CENÁRIO A — canary SAUDÁVEL (mesma distribuição do baseline)")
    print("=" * 70)
    # Sem regressão real: a versão nova sai da MESMA distribuição do stable.
    # Qualquer diferença no gráfico é ruído amostral, não regressão.
    canary_ok = gerar_amostra("canary-v2", 1200, taxa_erro=0.010, lat_media=120, lat_sigma=0.35)
    relatar(baseline, canary_ok)

    print("\n" + "=" * 70)
    print("CENÁRIO B — canary DEGRADADO (regressão de erro e latência)")
    print("=" * 70)
    canary_ruim = gerar_amostra("canary-v3", 1200, taxa_erro=0.055, lat_media=210, lat_sigma=0.45)
    relatar(baseline, canary_ruim)

    print("\n" + "=" * 70)
    print("💡 CONCLUSÃO")
    print("=" * 70)
    print("""
  Um canary "um pouco pior" não justifica rollback: pode ser só ruído.
  O p-value diz se a diferença é grande demais para ser sorte. Só
  revertemos quando a piora é estatisticamente significativa (p < alpha).

  Essa decisão é exatamente o que um AnalysisTemplate do Argo Rollouts
  automatiza a cada gate do canário.

  ➡️  Próximo vídeo (2.3): gerar o Rollout + AnalysisTemplate de verdade.
    """)


if __name__ == "__main__":
    executar()
