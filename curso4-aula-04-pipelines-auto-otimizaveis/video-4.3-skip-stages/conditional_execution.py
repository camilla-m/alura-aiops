"""
Vídeo 4.3 — Skip seguro de stages por análise de diff
================================================================
Recebe o conteúdo de um diff (lista de arquivos alterados) e um
conjunto de regras de impacto. Decide com segurança quais stages
podem ser pulados (ex.: mudança só em docs/ → skip build/test/deploy)
e alerta quando NÃO é seguro pular. A postura é fail-safe: na dúvida,
o stage roda.

Conceitos demonstrados:
- Classificação de mudanças por categoria de caminho de arquivo
- Regras de impacto ligando categorias aos stages afetados
- Decisão de skip seguro com política conservadora (fail-safe)
- Alerta explícito quando pular seria arriscado
"""

from dataclasses import dataclass, field
from enum import Enum


class Decision(str, Enum):
    RUN = "▶️  EXECUTAR"
    SKIP = "⏭️  PULAR"


# Categorias de mudança e o padrão de caminho que as identifica
CATEGORY_PATTERNS = {
    "docs":     ("docs/", ".md", "README"),
    "code":     ("src/", "app/", "lib/", ".py", ".js", ".go"),
    "test":     ("tests/", "test_", "_test.", "spec."),
    "infra":    ("terraform/", "k8s/", "Dockerfile", ".tf"),
    "config":   (".yml", ".yaml", ".json", ".toml", ".env"),
    "assets":   ("assets/", "static/", ".png", ".svg", ".css"),
}

# Para cada stage, quais categorias de mudança o tornam necessário.
# Se NENHUMA categoria do diff estiver aqui, o stage pode ser pulado.
STAGE_IMPACT = {
    "build":     {"code", "infra", "config"},
    "lint":      {"code", "test", "config"},
    "unit-test": {"code", "test"},
    "e2e-test":  {"code", "infra", "config"},
    "deploy":    {"code", "infra", "config", "assets"},
}

# Custo médio de cada stage (s) — usado para somar a economia dos skips
STAGE_COST = {"build": 180, "lint": 45, "unit-test": 420, "e2e-test": 240, "deploy": 90}


@dataclass
class SkipPlan:
    stage: str
    decision: Decision
    reason: str
    saved: float = 0.0


def classify_diff(changed_files: list[str]) -> set[str]:
    """Mapeia cada arquivo do diff para suas categorias de impacto."""
    categorias: set[str] = set()
    for arquivo in changed_files:
        casou = False
        for cat, padroes in CATEGORY_PATTERNS.items():
            if any(p in arquivo for p in padroes):
                categorias.add(cat)
                casou = True
        if not casou:
            categorias.add("desconhecido")   # fail-safe: força execução
    return categorias


def decide(changed_files: list[str]) -> list[SkipPlan]:
    """Decide RUN/SKIP para cada stage a partir das categorias do diff."""
    categorias = classify_diff(changed_files)
    plano: list[SkipPlan] = []

    for stage, gatilhos in STAGE_IMPACT.items():
        atingidas = categorias & gatilhos
        if "desconhecido" in categorias:
            plano.append(SkipPlan(stage, Decision.RUN,
                                  "diff contém arquivo não classificado (fail-safe)"))
        elif atingidas:
            plano.append(SkipPlan(stage, Decision.RUN,
                                  f"afetado por: {', '.join(sorted(atingidas))}"))
        else:
            plano.append(SkipPlan(stage, Decision.SKIP,
                                  "nenhuma categoria do diff impacta este stage",
                                  saved=STAGE_COST[stage]))
    return plano


CENARIOS = {
    "PR só de documentação": [
        "docs/guia-instalacao.md", "README.md",
    ],
    "Hotfix em um serviço": [
        "src/payment/charge.py", "tests/test_charge.py",
    ],
    "Mudança de infra": [
        "terraform/rds.tf", "k8s/deployment.yaml",
    ],
    "Arquivo fora do padrão": [
        "docs/changelog.md", "scripts/migração-manual.sh",
    ],
}


def run() -> None:
    print("=" * 70)
    print("🧭 Skip seguro de stages — decisão por análise de diff")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)

    for titulo, arquivos in CENARIOS.items():
        categorias = classify_diff(arquivos)
        plano = decide(arquivos)
        economia = sum(p.saved for p in plano)

        print("\n" + "─" * 70)
        print(f"📦 CENÁRIO: {titulo}")
        print("─" * 70)
        print(f"  Arquivos no diff : {', '.join(arquivos)}")
        print(f"  Categorias       : {', '.join(sorted(categorias))}\n")

        for p in plano:
            marca = "" if p.decision == Decision.RUN else f"  (economiza {p.saved:.0f}s)"
            print(f"    {p.decision.value}  {p.stage:<11} — {p.reason}{marca}")

        pulados = [p.stage for p in plano if p.decision == Decision.SKIP]
        if "desconhecido" in categorias:
            print(f"\n  ⚠️  ALERTA: arquivo fora do padrão conhecido no diff.")
            print(f"     Política fail-safe → NENHUM stage pulado (execução completa).")
        elif pulados:
            print(f"\n  ✅ Skip seguro de: {', '.join(pulados)} "
                  f"→ economia total de {economia:.0f}s ({economia/60:.1f} min)")
        else:
            print(f"\n  ▶️  Todos os stages são necessários neste diff.")

    print("\n" + "=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  A regra de ouro é assimétrica: pular um stage necessário quebra produção,
  então o custo de um falso 'skip' é altíssimo. Por isso a política é
  conservadora — só pulamos com evidência clara no diff, e qualquer arquivo
  não classificado força a execução completa.

  No Vídeo 4.4, um agente vai combinar gargalos, paralelismo, cache e skip
  para PROPOR melhorias estruturais no próprio pipeline.
    """)


if __name__ == "__main__":
    run()
