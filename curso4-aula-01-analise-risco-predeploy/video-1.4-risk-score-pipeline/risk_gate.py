"""
Vídeo 1.4 — Risk score no pipeline: o gate de CI
=================================================
Simula um gate de CI: recebe um deploy candidato, calcula o risk score
usando pesos já treinados (embutidos) e decide PASS / WARN / BLOCK com
thresholds configuráveis, escalando para revisão humana quando preciso.

Conceitos demonstrados:
- Cálculo do risk score a partir de pesos do modelo (logit → 0–100)
- Decisão por thresholds configuráveis (PASS / WARN / BLOCK)
- Escalonamento para revisão humana em WARN e BLOCK
- Saída no formato de log de pipeline CI + exit code lógico
"""

import math
from dataclasses import dataclass
from enum import Enum

# Pesos "congelados" de um modelo já treinado (ver vídeo 1.3).
# Aplicados sobre features padronizadas (z-score) com média/desvio de referência.
PESOS = {
    "churn":        0.95,
    "cobertura":   -1.35,
    "complexidade": 0.55,
    "n_arquivos":   0.70,
    "idade_codigo": 0.40,
    "termos_risco": 0.60,
}
INTERCEPTO = -0.8
# Média e desvio de referência do conjunto de treino (para padronizar)
REF_MEDIA = {"churn": 700, "cobertura": 0.40, "complexidade": 8.0, "n_arquivos": 15, "idade_codigo": 300, "termos_risco": 0.6}
REF_DESVIO = {"churn": 550, "cobertura": 0.22, "complexidade": 5.0, "n_arquivos": 11, "idade_codigo": 250, "termos_risco": 1.0}


class Decisao(str, Enum):
    PASS = "✅ PASS"
    WARN = "⚠️  WARN"
    BLOCK = "⛔ BLOCK"


@dataclass
class Thresholds:
    """Faixas de decisão, configuráveis por time/ambiente."""
    warn: int = 40   # score >= warn  → WARN
    block: int = 70  # score >= block → BLOCK


@dataclass
class DeployCandidato:
    nome: str
    churn: int
    cobertura: float
    complexidade: float
    n_arquivos: int
    idade_codigo: int
    termos_risco: int

    def features(self) -> dict:
        return {
            "churn": self.churn, "cobertura": self.cobertura,
            "complexidade": self.complexidade, "n_arquivos": self.n_arquivos,
            "idade_codigo": self.idade_codigo, "termos_risco": self.termos_risco,
        }


def calcular_score(cand: DeployCandidato) -> int:
    """Padroniza as features, aplica os pesos e devolve score 0–100."""
    z = INTERCEPTO
    for nome, valor in cand.features().items():
        padronizado = (valor - REF_MEDIA[nome]) / REF_DESVIO[nome]
        z += PESOS[nome] * padronizado
    prob = 1 / (1 + math.exp(-z))
    return round(prob * 100)


def decidir(score: int, th: Thresholds) -> Decisao:
    if score >= th.block:
        return Decisao.BLOCK
    if score >= th.warn:
        return Decisao.WARN
    return Decisao.PASS


def top_fatores(cand: DeployCandidato, n: int = 3) -> list[str]:
    """Fatores que mais empurraram o score para cima (explicabilidade)."""
    contrib = []
    for nome, valor in cand.features().items():
        padronizado = (valor - REF_MEDIA[nome]) / REF_DESVIO[nome]
        contrib.append((nome, PESOS[nome] * padronizado))
    contrib.sort(key=lambda c: c[1], reverse=True)
    return [f"{nome} (+{c:.2f})" for nome, c in contrib[:n] if c > 0]


def rodar_gate(cand: DeployCandidato, th: Thresholds) -> int:
    """Executa o gate e imprime como um passo de pipeline CI. Retorna exit code."""
    print("─" * 70)
    print(f"▶ ci/risk-gate :: candidato = {cand.nome}")
    print("─" * 70)
    print(f"  [1/4] Coletando features do deploy candidato...")
    print(f"        churn={cand.churn}  cobertura={cand.cobertura:.2f}  "
          f"arquivos={cand.n_arquivos}  complexidade={cand.complexidade:.1f}")
    print(f"  [2/4] Aplicando modelo de risco (pesos treinados)...")
    score = calcular_score(cand)
    print(f"  [3/4] Risk score computado: {score}/100  "
          f"(thresholds WARN>={th.warn} BLOCK>={th.block})")
    decisao = decidir(score, th)

    print(f"  [4/4] Decisão do gate: {decisao.value}")
    fatores = top_fatores(cand)
    if fatores:
        print(f"        Principais fatores de risco: {', '.join(fatores)}")

    if decisao == Decisao.PASS:
        print(f"  → Deploy liberado automaticamente. ✅")
        exit_code = 0
    elif decisao == Decisao.WARN:
        print(f"  → 🔔 Escalonando para REVISÃO HUMANA (aprovação de 1 revisor).")
        print(f"  → Deploy PAUSADO aguardando sign-off.")
        exit_code = 78  # convenção: "neutral / requer ação" em vários runners
    else:
        print(f"  → 🚨 Deploy BLOQUEADO. Requer revisão sênior + justificativa.")
        print(f"  → Pipeline falha para impedir a promoção à produção.")
        exit_code = 1
    print(f"  exit code = {exit_code}\n")
    return exit_code


def executar() -> None:
    print("=" * 70)
    print("🚦 Gate de CI orientado a risco de deploy")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)
    print("  Cada deploy passa pelo gate ANTES de ser promovido à produção.\n")

    th = Thresholds(warn=40, block=70)
    candidatos = [
        DeployCandidato("feat/tooltip-ajuste", churn=90, cobertura=0.62,
                        complexidade=3.5, n_arquivos=2, idade_codigo=60, termos_risco=0),
        DeployCandidato("feat/novo-checkout", churn=850, cobertura=0.25,
                        complexidade=11.0, n_arquivos=18, idade_codigo=420, termos_risco=1),
        DeployCandidato("refactor/migration-billing", churn=1800, cobertura=0.05,
                        complexidade=21.0, n_arquivos=39, idade_codigo=830, termos_risco=3),
    ]

    codes = [rodar_gate(c, th) for c in candidatos]

    print("=" * 70)
    print("📌 RESUMO DO GATE")
    print("=" * 70)
    print(f"  Deploys avaliados: {len(codes)}")
    print(f"  Liberados (PASS):  {codes.count(0)}")
    print(f"  Em revisão (WARN): {codes.count(78)}")
    print(f"  Bloqueados (BLOCK):{codes.count(1)}")
    print("""
  O gate não substitui o humano: ele filtra o óbvio (PASS) e concentra
  atenção onde o risco é real (WARN/BLOCK). Thresholds são ajustáveis por
  ambiente — produção pode exigir BLOCK>=60, um sandbox pode nem barrar.

  ➡️  Próximo vídeo (1.5): juntar dados + modelo + gate em um pipeline único.
    """)


if __name__ == "__main__":
    executar()
