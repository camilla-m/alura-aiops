"""
Vídeo 1.2 — Features preditivas: o que torna um deploy perigoso
================================================================
A partir de um lote simulado de PRs (mensagem + estatísticas de diff),
extrai um feature vector por PR e ranqueia quais features mais se
associam a falha via correlação simples de Pearson.

Conceitos demonstrados:
- Extração de features: code churn, cobertura, complexidade, nº de arquivos, idade
- Montagem de um feature vector numérico por PR
- Correlação (Pearson) de cada feature com o desfecho (falhou/passou)
- Ranking de poder preditivo — quais sinais o modelo deve valorizar
"""

import random
from dataclasses import dataclass, field

import numpy as np

random.seed(42)
np.random.seed(42)

# Palavras que sugerem lógica de controle de fluxo — proxy de complexidade
PALAVRAS_CONTROLE = ("if", "for", "while", "case", "try", "catch", "&&", "||")
# Termos de commit que costumam sinalizar risco
TERMOS_RISCO = ("hotfix", "refactor", "migration", "revert", "wip", "urgent")


@dataclass
class PullRequest:
    """PR bruto: o que sai da API do provedor de código."""
    id: str
    mensagem: str
    linhas_add: int
    linhas_del: int
    arquivos: int
    linhas_teste: int          # linhas tocadas em arquivos *_test / spec
    tokens_controle: int       # ocorrências de if/for/while... no diff
    idade_codigo_dias: int     # idade média do código tocado (git blame)
    falhou: bool = False


@dataclass
class FeatureVector:
    """PR já traduzido para números que o modelo entende."""
    pr_id: str
    churn: int                 # add + del
    ratio_cobertura: float     # linhas_teste / churn
    complexidade: float        # tokens_controle / arquivos
    n_arquivos: int
    idade_codigo: int
    termos_risco: int
    alvo: int = 0              # 1 = falhou, 0 = ok
    valores: dict = field(default_factory=dict)


def gerar_prs(n: int = 120) -> list[PullRequest]:
    """Simula PRs com desfecho correlacionado às features."""
    prs: list[PullRequest] = []
    for i in range(n):
        arquivos = random.randint(1, 40)
        churn_base = arquivos * random.randint(5, 60)
        linhas_add = int(churn_base * random.uniform(0.4, 0.9))
        linhas_del = churn_base - linhas_add
        tem_teste = random.random() < 0.7
        linhas_teste = random.randint(5, max(6, linhas_add // 2)) if tem_teste else 0
        tokens_controle = int((linhas_add / 10) * random.uniform(0.5, 2.5))
        idade = random.randint(3, 900)
        termos = [t for t in TERMOS_RISCO if random.random() < 0.18]
        msg = f"{'/'.join(termos) or 'feat'}: alteração {i}"

        # Probabilidade de falha (só para simular o histórico)
        cobertura = linhas_teste / max(1, linhas_add + linhas_del)
        p = 0.05 + 0.25 * (arquivos > 20) + 0.20 * (cobertura < 0.1)
        p += 0.15 * (tokens_controle > 80) + 0.10 * (idade > 500)
        p += 0.08 * len(termos)
        falhou = random.random() < min(p, 0.95)

        prs.append(PullRequest(
            id=f"PR-{1000 + i}", mensagem=msg,
            linhas_add=linhas_add, linhas_del=linhas_del, arquivos=arquivos,
            linhas_teste=linhas_teste, tokens_controle=tokens_controle,
            idade_codigo_dias=idade, falhou=falhou,
        ))
    return prs


def extrair_features(pr: PullRequest) -> FeatureVector:
    """Converte um PR bruto em um feature vector numérico."""
    churn = pr.linhas_add + pr.linhas_del
    ratio_cobertura = round(pr.linhas_teste / max(1, churn), 3)
    complexidade = round(pr.tokens_controle / max(1, pr.arquivos), 2)
    termos_risco = sum(t in pr.mensagem.lower() for t in TERMOS_RISCO)

    fv = FeatureVector(
        pr_id=pr.id, churn=churn, ratio_cobertura=ratio_cobertura,
        complexidade=complexidade, n_arquivos=pr.arquivos,
        idade_codigo=pr.idade_codigo_dias, termos_risco=termos_risco,
        alvo=int(pr.falhou),
    )
    fv.valores = {
        "churn": churn, "cobertura": ratio_cobertura,
        "complexidade": complexidade, "n_arquivos": pr.arquivos,
        "idade_codigo": pr.idade_codigo_dias, "termos_risco": termos_risco,
    }
    return fv


def correlacao(coluna: list[float], alvo: list[int]) -> float:
    """Correlação de Pearson entre uma feature e o desfecho."""
    if np.std(coluna) == 0:
        return 0.0
    return float(np.corrcoef(coluna, alvo)[0, 1])


def executar() -> None:
    print("=" * 70)
    print("🧬 Extração de features preditivas de Pull Requests")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)

    prs = gerar_prs(120)
    vetores = [extrair_features(pr) for pr in prs]

    print(f"\n  PRs processados: {len(prs)}")
    print("\n" + "─" * 70)
    print("📋 FEATURE VECTORS (amostra dos 6 primeiros PRs)")
    print("─" * 70)
    cab = f"  {'PR':<9}{'churn':>7}{'cobert.':>9}{'complex':>9}{'arqs':>6}{'idade':>7}{'risco':>7}{'alvo':>7}"
    print(cab)
    print("  " + "─" * (len(cab) - 2))
    for fv in vetores[:6]:
        alvo = "FALHA" if fv.alvo else "ok"
        print(f"  {fv.pr_id:<9}{fv.churn:>7}{fv.ratio_cobertura:>9.2f}"
              f"{fv.complexidade:>9.1f}{fv.n_arquivos:>6}{fv.idade_codigo:>7}"
              f"{fv.termos_risco:>7}{alvo:>7}")

    # --- Ranking por correlação com falha ---
    print("\n" + "─" * 70)
    print("📈 QUAIS FEATURES MAIS SE ASSOCIAM A FALHA (correlação de Pearson)")
    print("─" * 70)
    print("  |corr| perto de 0 = pouco preditiva | perto de 1 = forte sinal\n")

    nomes = ["churn", "cobertura", "complexidade", "n_arquivos", "idade_codigo", "termos_risco"]
    alvo = [fv.alvo for fv in vetores]
    ranking = []
    for nome in nomes:
        coluna = [fv.valores[nome] for fv in vetores]
        ranking.append((nome, correlacao(coluna, alvo)))

    for nome, corr in sorted(ranking, key=lambda x: abs(x[1]), reverse=True):
        sinal = "↑ aumenta risco" if corr > 0 else "↓ reduz risco"
        barra = "█" * round(abs(corr) * 40)
        print(f"  {nome:<14} corr={corr:+.3f}  {sinal:<16} {barra}")

    print("\n" + "=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  As features não têm o mesmo peso: nº de arquivos e code churn costumam
  dominar o sinal, com cobertura de testes puxando o risco para baixo.

  Correlação simples já mostra a DIREÇÃO de cada feature, mas trata uma
  de cada vez. Um modelo aprende os pesos em CONJUNTO, considerando as
  interações entre elas.

  ➡️  Próximo vídeo (1.3): treinar um modelo de risco sobre esses vetores.
    """)


if __name__ == "__main__":
    executar()
