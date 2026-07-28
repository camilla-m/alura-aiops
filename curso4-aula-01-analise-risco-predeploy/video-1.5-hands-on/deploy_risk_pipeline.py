"""
Vídeo 1.5 — Hands-on: pipeline de risco de ponta a ponta
=========================================================
Junta tudo da aula em uma execução: gera o dataset histórico, treina o
modelo de risco e roda o gate de CI em 3 PRs de exemplo (seguro, médio
e perigoso), mostrando a decisão e o racional de cada um.

Conceitos demonstrados:
- Pipeline end-to-end: dataset → treino → risk score → decisão de gate
- Reuso do modelo treinado para pontuar PRs novos (nunca vistos)
- Racional explicável por trás de cada veredito (features dominantes)
- Fechamento da aula de análise de risco pré-deploy
"""

from dataclasses import dataclass
from enum import Enum

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

np.random.seed(42)

FEATURES = ["churn", "cobertura", "complexidade", "n_arquivos", "idade_codigo", "termos_risco"]


class Decisao(str, Enum):
    PASS = "✅ PASS"
    WARN = "⚠️  WARN"
    BLOCK = "⛔ BLOCK"


@dataclass
class PR:
    nome: str
    churn: int
    cobertura: float
    complexidade: float
    n_arquivos: int
    idade_codigo: int
    termos_risco: int

    def vetor(self) -> list[float]:
        return [self.churn, self.cobertura, self.complexidade,
                self.n_arquivos, self.idade_codigo, self.termos_risco]


# --- Etapa 1: dados históricos -------------------------------------------------
def gerar_dataset(n: int = 400):
    churn = np.random.randint(20, 2000, n)
    cobertura = np.clip(np.random.beta(2, 3, n), 0, 1)
    complexidade = np.random.gamma(3, 2, n)
    n_arquivos = np.random.randint(1, 45, n)
    idade_codigo = np.random.randint(3, 900, n)
    termos_risco = np.random.poisson(0.6, n)
    X = np.column_stack([churn, cobertura, complexidade, n_arquivos, idade_codigo, termos_risco])
    z = (-2.4 + 0.0011 * churn - 3.0 * cobertura + 0.07 * complexidade
         + 0.045 * n_arquivos + 0.0011 * idade_codigo + 0.35 * termos_risco)
    y = (np.random.random(n) < 1 / (1 + np.exp(-z))).astype(int)
    return X, y


# --- Etapa 2: treino ----------------------------------------------------------
def treinar():
    X, y = gerar_dataset(400)
    scaler = StandardScaler().fit(X)
    model = LogisticRegression(max_iter=1000).fit(scaler.transform(X), y)
    return model, scaler, y.mean()


# --- Etapa 3: score + gate ----------------------------------------------------
def pontuar(model, scaler, pr: PR) -> int:
    prob = model.predict_proba(scaler.transform([pr.vetor()]))[0, 1]
    return round(prob * 100)


def decidir(score: int, warn: int = 40, block: int = 70) -> Decisao:
    if score >= block:
        return Decisao.BLOCK
    if score >= warn:
        return Decisao.WARN
    return Decisao.PASS


def racional(model, scaler, pr: PR, n: int = 3) -> list[str]:
    """Features que mais contribuíram para o score deste PR."""
    z = scaler.transform([pr.vetor()])[0]
    contrib = sorted(zip(FEATURES, model.coef_[0] * z), key=lambda c: c[1], reverse=True)
    return [f"{nome} (+{c:.2f})" for nome, c in contrib[:n] if c > 0]


def executar() -> None:
    print("=" * 70)
    print("🛠️  Pipeline de risco de deploy — end-to-end")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)

    print("\n  [Etapa 1] Gerando dataset histórico de deploys...")
    print("  [Etapa 2] Treinando modelo de risco (LogisticRegression)...")
    model, scaler, taxa = treinar()
    print(f"            Modelo treinado. Taxa de falha histórica: {taxa*100:.1f}%")

    print("  [Etapa 3] Rodando o gate de CI em 3 PRs de exemplo...\n")

    prs = [
        PR("PR-#seguro    docs+tooltip", churn=70, cobertura=0.70,
           complexidade=2.5, n_arquivos=2, idade_codigo=45, termos_risco=0),
        PR("PR-#medio     nova feature", churn=780, cobertura=0.28,
           complexidade=10.0, n_arquivos=16, idade_codigo=380, termos_risco=1),
        PR("PR-#perigoso  migration billing", churn=1850, cobertura=0.04,
           complexidade=22.0, n_arquivos=40, idade_codigo=860, termos_risco=3),
    ]

    resultados = []
    for pr in prs:
        score = pontuar(model, scaler, pr)
        decisao = decidir(score)
        resultados.append((pr, score, decisao))

        print("─" * 70)
        print(f"  {pr.nome}")
        marcador = "🟢" if score < 40 else ("🟡" if score < 70 else "🔴")
        print(f"    risk score = {marcador} {score}/100   →   {decisao.value}")
        fatores = racional(model, scaler, pr)
        if fatores:
            print(f"    racional: {', '.join(fatores)}")
        if decisao == Decisao.PASS:
            print(f"    ação: liberar deploy automaticamente")
        elif decisao == Decisao.WARN:
            print(f"    ação: pausar e escalar para 1 revisor")
        else:
            print(f"    ação: bloquear e exigir revisão sênior + justificativa")
    print("─" * 70)

    # --- Fechamento ---
    print("\n" + "=" * 70)
    print("📌 FECHAMENTO DA AULA")
    print("=" * 70)
    resumo = ", ".join(f"{pr.nome.split()[0]}={dec.value.strip()}" for pr, _, dec in resultados)
    print(f"\n  Vereditos: {resumo}")
    print("""
  Do histórico de falhas (1.1) às features (1.2), ao modelo (1.3) e ao
  gate (1.4), chegamos a um pipeline que barra o deploy perigoso ANTES da
  produção — com um número explicável, não um palpite.

  O mesmo modelo tratou os 3 PRs de forma coerente: liberou o trivial,
  pediu revisão no intermediário e travou o de altíssimo risco.

  ➡️  Próxima aula: automatizar rollback e resposta quando o risco escapa
      do gate e chega em produção.
    """)


if __name__ == "__main__":
    executar()
