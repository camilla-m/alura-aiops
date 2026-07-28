"""
Vídeo 2.5 — Hands-on: rollout canário de ponta a ponta
========================================================
EXERCÍCIO PRÁTICO FINAL — Aula 2 / Curso 4

Junta tudo o que vimos na aula num único rollout canário automatizado:
  2.1 estratégia canária (steps de peso)
  2.2 canary analysis com significância estatística
  2.3 gates de análise no estilo Argo Rollouts
  2.4 promoção ou rollback automático a cada gate

Fluxo:
  para cada step de peso → gera tráfego sintético (baseline vs canary)
  → roda a canary analysis → decide avançar ou abortar → relatório final.

Execute:
  python progressive_delivery_lab.py
"""

import math
import random
from dataclasses import dataclass
from enum import Enum

random.seed(42)

APP = "mapi-api"
ALPHA = 0.05
STEPS_PESO = [5, 20, 50, 100]  # degraus do canário
REQS_POR_GATE = 800            # requisições por grupo em cada gate


class Veredito(str, Enum):
    PROMOTE = "✅ PROMOTE"
    ROLLBACK = "❌ ROLLBACK"


@dataclass
class Telemetria:
    erros: int
    total: int
    latencias: list[float]

    @property
    def error_rate(self) -> float:
        return self.erros / self.total if self.total else 0.0

    @property
    def p95(self) -> float:
        ordenados = sorted(self.latencias)
        k = (len(ordenados) - 1) * 0.95
        baixo, alto = math.floor(k), math.ceil(k)
        if baixo == alto:
            return ordenados[int(k)]
        return ordenados[baixo] + (ordenados[alto] - ordenados[baixo]) * (k - baixo)


@dataclass
class GateReport:
    peso: int
    baseline: Telemetria
    canary: Telemetria
    p_erro: float
    p_lat: float
    veredito: Veredito


def _phi(z: float) -> float:
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def ztest_proporcao(base: Telemetria, can: Telemetria) -> float:
    """p-value (uma cauda) de o erro do canary ser maior que o do baseline."""
    p_pool = (base.erros + can.erros) / (base.total + can.total)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / base.total + 1 / can.total))
    if se == 0:
        return 1.0
    z = (can.error_rate - base.error_rate) / se
    return 1 - _phi(z)


def mann_whitney(base: list[float], can: list[float]) -> float:
    """p-value (uma cauda) de a latência do canary ser maior — aprox. normal."""
    n1, n2 = len(can), len(base)
    marcados = sorted([(v, "c") for v in can] + [(v, "b") for v in base])
    soma = 0.0
    for rank, (_, g) in enumerate(marcados, start=1):
        if g == "c":
            soma += rank
    u = soma - n1 * (n1 + 1) / 2
    mu = n1 * n2 / 2
    sigma = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    z = (u - mu) / sigma if sigma else 0.0
    return 1 - _phi(z)


def gerar_trafego(taxa_erro: float, lat_media: float, sigma: float) -> Telemetria:
    erros = sum(1 for _ in range(REQS_POR_GATE) if random.random() < taxa_erro)
    lat = [max(1.0, random.lognormvariate(math.log(lat_media), sigma))
           for _ in range(REQS_POR_GATE)]
    return Telemetria(erros, REQS_POR_GATE, lat)


def rodar_gate(peso: int, canary_saudavel: bool) -> GateReport:
    baseline = gerar_trafego(0.010, 120, 0.35)
    if canary_saudavel:
        # Sem regressão real: mesma distribuição do baseline (só ruído).
        canary = gerar_trafego(0.010, 120, 0.35)
    else:
        canary = gerar_trafego(0.060, 230, 0.45)

    p_erro = ztest_proporcao(baseline, canary)
    p_lat = mann_whitney(baseline.latencias, canary.latencias)
    erro_pior = canary.error_rate > baseline.error_rate and p_erro < ALPHA
    lat_pior = canary.p95 > baseline.p95 and p_lat < ALPHA
    veredito = Veredito.ROLLBACK if (erro_pior or lat_pior) else Veredito.PROMOTE
    return GateReport(peso, baseline, canary, p_erro, p_lat, veredito)


def imprimir_gate(g: GateReport) -> None:
    print(f"\n  🚦 GATE — canary em {g.peso}% do tráfego")
    print(f"     {'':13}{'baseline':>10}{'canary':>10}{'p-value':>10}")
    print(f"     error_rate {g.baseline.error_rate*100:>8.2f}%"
          f"{g.canary.error_rate*100:>9.2f}%{g.p_erro:>10.4f}")
    print(f"     p95 (ms)   {g.baseline.p95:>9.0f}{g.canary.p95:>10.0f}{g.p_lat:>10.4f}")
    print(f"     → análise: {g.veredito.value}")


def executar(canary_saudavel: bool = True) -> None:
    print("=" * 70)
    print("🧪 HANDS-ON: rollout canário de ponta a ponta")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)
    print(f"\n  App: {APP}  |  steps de peso: {STEPS_PESO}  |  alpha={ALPHA}")
    print(f"  A cada gate: gera tráfego, roda canary analysis e decide.\n")

    historico: list[GateReport] = []
    promovido = True
    for peso in STEPS_PESO:
        g = rodar_gate(peso, canary_saudavel)
        historico.append(g)
        imprimir_gate(g)
        if g.veredito is Veredito.ROLLBACK:
            promovido = False
            print(f"\n  🚨 Abortando rollout no peso {peso}% — revertendo para o stable.")
            break

    # --- Relatório final ---
    print("\n" + "=" * 70)
    print("📋 RELATÓRIO FINAL DO ROLLOUT")
    print("=" * 70)
    gates_ok = sum(1 for g in historico if g.veredito is Veredito.PROMOTE)
    print(f"\n  Gates avaliados     : {len(historico)}")
    print(f"  Gates aprovados     : {gates_ok}")
    peso_final = 100 if promovido else historico[-1].peso
    if promovido:
        print(f"  Desfecho            : ✅ PROMOVIDO a 100% — nova versão é o stable")
        print(f"  Blast radius máximo : contido em cada degrau ({STEPS_PESO})")
    else:
        print(f"  Desfecho            : ❌ REVERTIDO no peso {peso_final}%")
        print(f"  Blast radius        : limitado a {peso_final}% do tráfego "
              f"(o resto nunca viu a versão ruim)")

    print("\n  🧰 Técnicas da aula aplicadas:")
    print("     ✔ 2.1 estratégia canária em degraus de peso")
    print("     ✔ 2.2 canary analysis com z-test + Mann-Whitney")
    print("     ✔ 2.3 gates de análise no estilo Argo Rollouts")
    print("     ✔ 2.4 promoção/rollback automático a cada gate")

    print("\n" + "=" * 70)
    print("🎓 AULA 2 CONCLUÍDA — PROGRESSIVE DELIVERY ASSISTIDO!")
    print("=" * 70)
    print("""
  Você saiu de "deploy no escuro" para um release que se defende sozinho:
  a versão nova só avança se as métricas provarem, com significância
  estatística, que ela é tão boa quanto a atual — e se reverte sozinha
  quando não é.

  "Um bom rollout não é o que nunca falha, é o que falha para 5% dos
   usuários por 30 segundos, em vez de para 100% por 30 minutos."
    """)


if __name__ == "__main__":
    # Troque para False para ver o rollout abortar num canary degradado.
    executar(canary_saudavel=True)
