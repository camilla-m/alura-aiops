"""
Vídeo 1.3 — Um modelo de risco de deploy com regressão logística
=================================================================
Treina uma LogisticRegression sobre um dataset sintético de deploys e
transforma a probabilidade prevista em um risk score de 0 a 100.

Conceitos demonstrados:
- Treino de LogisticRegression (scikit-learn) sobre features padronizadas
- Conversão probabilidade → risk score 0–100 legível
- Avaliação: acurácia e matriz de confusão simplificada
- Interpretabilidade: pesos das features explicam cada score
"""

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

np.random.seed(42)

# Ordem das features usada em todo o script (e reaproveitada nos vídeos 1.4/1.5)
FEATURES = ["churn", "cobertura", "complexidade", "n_arquivos", "idade_codigo", "termos_risco"]


def gerar_dataset(n: int = 400):
    """Gera (X, y) sintético de deploys com relação features→falha realista."""
    churn = np.random.randint(20, 2000, n)
    cobertura = np.clip(np.random.beta(2, 3, n), 0, 1)          # 0..1
    complexidade = np.random.gamma(3, 2, n)                     # ~0..25
    n_arquivos = np.random.randint(1, 45, n)
    idade_codigo = np.random.randint(3, 900, n)
    termos_risco = np.random.poisson(0.6, n)

    X = np.column_stack([churn, cobertura, complexidade, n_arquivos, idade_codigo, termos_risco])

    # Logit "verdadeiro" (desconhecido do modelo) que gera os rótulos
    z = (
        -2.4
        + 0.0011 * churn
        - 3.0 * cobertura
        + 0.07 * complexidade
        + 0.045 * n_arquivos
        + 0.0011 * idade_codigo
        + 0.35 * termos_risco
    )
    prob = 1 / (1 + np.exp(-z))
    y = (np.random.random(n) < prob).astype(int)
    return X, y


def risk_score(model: LogisticRegression, scaler: StandardScaler, X: np.ndarray) -> np.ndarray:
    """Probabilidade de falha prevista, reescalada para 0–100."""
    prob = model.predict_proba(scaler.transform(X))[:, 1]
    return np.round(prob * 100).astype(int)


def executar() -> None:
    print("=" * 70)
    print("🤖 Modelo de risco de deploy (Regressão Logística)")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)

    X, y = gerar_dataset(400)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    scaler = StandardScaler().fit(X_tr)
    model = LogisticRegression(max_iter=1000)
    model.fit(scaler.transform(X_tr), y_tr)

    print(f"\n  Dataset: {len(X)} deploys  |  treino={len(X_tr)}  teste={len(X_te)}")
    print(f"  Taxa de falha no dataset: {y.mean()*100:.1f}%")

    # --- Avaliação ---
    y_pred = model.predict(scaler.transform(X_te))
    acc = accuracy_score(y_te, y_pred)
    tn, fp, fn, tp = confusion_matrix(y_te, y_pred).ravel()

    print("\n" + "─" * 70)
    print("📊 AVALIAÇÃO NO CONJUNTO DE TESTE")
    print("─" * 70)
    print(f"  Acurácia: {acc*100:.1f}%")
    print("\n  Matriz de confusão:")
    print("                     previsto: OK   previsto: FALHA")
    print(f"    real: OK      {tn:>12}   {fp:>15}")
    print(f"    real: FALHA   {fn:>12}   {tp:>15}")
    precisao = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    print(f"\n  Precisão (falhas previstas que eram reais): {precisao*100:.1f}%")
    print(f"  Recall   (falhas reais que pegamos):        {recall*100:.1f}%")

    # --- Interpretabilidade ---
    print("\n" + "─" * 70)
    print("🔍 PESOS DAS FEATURES (por que o modelo dá determinado score)")
    print("─" * 70)
    print("  Coeficientes sobre features padronizadas → comparáveis entre si.\n")
    coefs = list(zip(FEATURES, model.coef_[0]))
    for nome, w in sorted(coefs, key=lambda c: abs(c[1]), reverse=True):
        direcao = "↑ aumenta risco" if w > 0 else "↓ reduz risco"
        barra = "█" * round(abs(w) * 12)
        print(f"  {nome:<14} peso={w:+.2f}  {direcao:<16} {barra}")

    # --- Score em exemplos ---
    print("\n" + "─" * 70)
    print("🎯 RISK SCORE 0–100 EM DEPLOYS DE EXEMPLO")
    print("─" * 70)
    exemplos = np.array([
        [120, 0.55, 4.0, 3, 90, 0],     # pequeno, bem testado
        [800, 0.15, 12.0, 22, 400, 1],  # médio, pouca cobertura
        [1900, 0.03, 22.0, 40, 850, 3], # enorme, sem teste, arriscado
    ])
    rotulos = ["deploy seguro     ", "deploy intermediário", "deploy perigoso   "]
    scores = risk_score(model, scaler, exemplos)
    for rotulo, s in zip(rotulos, scores):
        marcador = "🟢" if s < 30 else ("🟡" if s < 70 else "🔴")
        print(f"  {marcador} {rotulo}  risk score = {s:>3}/100")

    print("\n" + "=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  O modelo aprendeu os pesos que antes estimávamos na mão. A saída não é
  só "vai falhar / não vai": é uma PROBABILIDADE calibrada, virada em um
  score de 0 a 100 e explicável pelos coeficientes.

  Score interpretável = confiança do time. Dá para responder "por que 82?"
  apontando cobertura baixa + muitos arquivos, não uma caixa-preta.

  ➡️  Próximo vídeo (1.4): usar esse score como GATE dentro do pipeline CI.
    """)


if __name__ == "__main__":
    executar()
