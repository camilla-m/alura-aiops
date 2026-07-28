"""
Vídeo 2.1 — Progressive delivery: canary, blue-green e feature flags
=====================================================================
Simula o rollout de uma mesma versão nova usando três estratégias
diferentes e mostra, ao longo do tempo, quantos usuários ficam
expostos e qual seria o blast radius se a versão estivesse quebrada.

Conceitos demonstrados:
- Progressive delivery: expor a mudança de forma gradual e controlada
- Canary vs blue-green vs feature flags (mecânica e trade-offs)
- Blast radius: fração de usuários atingidos se a versão nova falhar
- Por que exposição gradual reduz o custo de um deploy ruim
"""

import random
from dataclasses import dataclass
from enum import Enum

random.seed(42)

TOTAL_USUARIOS = 100_000  # base de usuários atingida pelo release


class Estrategia(str, Enum):
    CANARY = "🐤 CANARY"
    BLUE_GREEN = "🔵🟢 BLUE-GREEN"
    FEATURE_FLAG = "🚩 FEATURE FLAG"


@dataclass
class Passo:
    """Um instante do rollout: quanto tempo passou e a exposição atual."""
    minuto: int
    exposicao: float  # fração de usuários na versão nova (0.0–1.0)
    nota: str

    @property
    def usuarios(self) -> int:
        return round(exposicao_para_usuarios(self.exposicao))


def exposicao_para_usuarios(fracao: float) -> float:
    return fracao * TOTAL_USUARIOS


# ---------------------------------------------------------------------------
# Cada estratégia é uma sequência de passos de exposição ao longo do tempo
# ---------------------------------------------------------------------------

def rollout_canary() -> list[Passo]:
    """Aumenta a exposição em degraus, com pausas para observar métricas."""
    return [
        Passo(0, 0.00, "deploy da versão nova, 0% de tráfego"),
        Passo(2, 0.05, "5% — primeiro degrau, observando métricas"),
        Passo(10, 0.20, "20% — canary analysis passou no gate"),
        Passo(20, 0.50, "50% — segundo gate ok"),
        Passo(30, 1.00, "100% — promovido, stable substituído"),
    ]


def rollout_blue_green() -> list[Passo]:
    """Mantém dois ambientes; troca 0% → 100% de uma vez no cutover."""
    return [
        Passo(0, 0.00, "green (novo) sobe em paralelo ao blue, sem tráfego"),
        Passo(5, 0.00, "smoke tests no green, ainda 0% de usuários reais"),
        Passo(6, 1.00, "cutover instantâneo: todo tráfego vai para o green"),
        Passo(30, 1.00, "blue fica de pé como rollback rápido"),
    ]


def rollout_feature_flag() -> list[Passo]:
    """Código já em produção; a flag liga a feature para coortes."""
    return [
        Passo(0, 0.00, "código deployado com a flag DESLIGADA para todos"),
        Passo(2, 0.01, "1% — liga para usuários internos (dogfooding)"),
        Passo(8, 0.10, "10% — coorte beta segmentada por atributo"),
        Passo(18, 0.50, "50% — rollout por porcentagem"),
        Passo(30, 1.00, "100% — flag ligada para todos (default on)"),
    ]


def desenhar_exposicao(fracao: float, largura: int = 24) -> str:
    cheias = round(fracao * largura)
    return "█" * cheias + "░" * (largura - cheias)


def simular(estrategia: Estrategia, passos: list[Passo]) -> None:
    print(f"\n{'─' * 70}")
    print(f"  {estrategia.value}")
    print(f"{'─' * 70}")
    print(f"  {'t':>4}  {'exposição':<26} {'usuários':>9}  {'blast':>6}")
    for p in passos:
        blast = p.exposicao  # se a versão nova quebra AGORA, este é o raio
        print(
            f"  {p.minuto:>3}m  {desenhar_exposicao(p.exposicao)} "
            f"{p.exposicao*100:>4.0f}%  {p.usuarios:>9,}  {blast*100:>4.0f}%"
        )
        print(f"        └─ {p.nota}")


def blast_radius_medio(passos: list[Passo]) -> float:
    """
    Exposição média ANTES de atingir 100%: aproxima a chance de um
    usuário "aleatório" já estar na versão nova quando o bug aparece.
    Quanto menor, menos gente é atingida por um deploy ruim.
    """
    parciais = [p.exposicao for p in passos if p.exposicao < 1.0]
    return sum(parciais) / len(parciais) if parciais else 1.0


def tempo_total(passos: list[Passo]) -> int:
    return passos[-1].minuto


def executar() -> None:
    print("=" * 70)
    print("🚚 Progressive delivery: expondo a versão nova aos poucos")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)
    print(f"\n  Mesma versão nova, {TOTAL_USUARIOS:,} usuários, três estratégias.")
    print("  A coluna 'blast' = % de usuários atingidos se a versão quebrar naquele instante.")

    estrategias = {
        Estrategia.CANARY: rollout_canary(),
        Estrategia.BLUE_GREEN: rollout_blue_green(),
        Estrategia.FEATURE_FLAG: rollout_feature_flag(),
    }
    for estrategia, passos in estrategias.items():
        simular(estrategia, passos)

    # --- Tabela comparativa ---
    print("\n" + "=" * 70)
    print("📊 COMPARATIVO DAS ESTRATÉGIAS")
    print("=" * 70)
    linhas = [
        # (aspecto, canary, blue-green, feature flag)
        ("Velocidade p/ 100%", "Média (degraus)", "Instantânea", "Média (por coorte)"),
        ("Custo de infra",     "Baixo (+1 réplica)", "Alto (2x ambiente)", "Baixo (mesmo deploy)"),
        ("Blast radius",       "Muito baixo",      "Alto no cutover",   "Muito baixo"),
        ("Granularidade",      "% de tráfego",     "Tudo ou nada",      "Usuário / atributo"),
        ("Rollback",           "Baixar o peso",    "Voltar p/ o blue",  "Desligar a flag"),
        ("Precisa redeploy?",  "Sim",              "Sim",               "Não (só a flag)"),
    ]
    print(f"\n  {'Aspecto':<20} {'Canary':<20} {'Blue-Green':<20} {'Feature Flag':<20}")
    print(f"  {'─'*20} {'─'*20} {'─'*20} {'─'*20}")
    for aspecto, c, bg, ff in linhas:
        print(f"  {aspecto:<20} {c:<20} {bg:<20} {ff:<20}")

    print("\n" + "─" * 70)
    print("🎯 Blast radius médio (exposição enquanto ainda não é 100%)")
    print("─" * 70)
    for estrategia, passos in estrategias.items():
        br = blast_radius_medio(passos)
        print(
            f"  {estrategia.value:<18} blast médio {br*100:4.0f}%  "
            f"(~{round(br*TOTAL_USUARIOS):>6,} usuários)  "
            f"tempo até 100%: {tempo_total(passos)}m"
        )

    print("\n" + "=" * 70)
    print("💡 CONCLUSÃO")
    print("=" * 70)
    print("""
  O blue-green é rápido para reverter, mas o cutover expõe 100% dos
  usuários de uma vez: se o green estiver quebrado, o blast radius é total.

  Canary e feature flags trocam um pouco de velocidade por segurança:
  a versão nova cresce em degraus e um bug atinge só a fração já exposta.

  A pergunta que fica: como decidir, a cada degrau, se é seguro subir o
  peso ou se é hora de reverter? É aí que entra a CANARY ANALYSIS.

  ➡️  Próximo vídeo (2.2): comparar baseline vs canary com estatística.
    """)


if __name__ == "__main__":
    executar()
