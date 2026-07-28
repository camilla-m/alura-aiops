"""
Vídeo 5.5 — Estratégia de adoção de CI/CD inteligente
======================================================
Scorecard de maturidade de CI/CD inteligente. Avalia uma organização
de exemplo em 5 dimensões, cada uma com níveis 0–4, identifica os gaps
em relação ao nível-alvo e gera um roadmap de adoção priorizado por
quick wins (relação impacto x esforço).

Fecha o CURSO 4 — CI/CD Inteligente, amarrando as ferramentas vistas:
- Risco pré-deploy       → Harness Continuous Verification (Vídeo 5.1)
- Progressive delivery   → Argo Rollouts (Vídeo 5.2)
- Feature management     → LaunchDarkly (Vídeo 5.3)
- Test intelligence      → Buildkite Test Analytics (Vídeo 5.4)
- Pipeline optimization  → cache, paralelismo, test selection

Conceitos demonstrados:
- Dataclasses/enums para dimensões e níveis de maturidade
- Cálculo de gap (atual vs. alvo) por dimensão
- Score global ponderado
- Priorização de roadmap por impacto/esforço (quick wins primeiro)
"""

from dataclasses import dataclass, field
from enum import IntEnum


class Level(IntEnum):
    AUSENTE = 0
    INICIAL = 1
    DEFINIDO = 2
    GERENCIADO = 3
    OTIMIZADO = 4


LEVEL_LABEL = {
    Level.AUSENTE:    "0 Ausente",
    Level.INICIAL:    "1 Inicial",
    Level.DEFINIDO:   "2 Definido",
    Level.GERENCIADO: "3 Gerenciado",
    Level.OTIMIZADO:  "4 Otimizado",
}


@dataclass
class Dimension:
    name: str
    tool: str
    weight: float          # importância relativa no score global
    current: Level
    target: Level
    # descrição do que caracteriza cada nível (0..4)
    ladder: list[str] = field(default_factory=list)
    # ação recomendada e esforço estimado (1=baixo .. 5=alto) para subir 1 nível
    next_action: str = ""
    effort: int = 3

    @property
    def gap(self) -> int:
        return max(0, self.target - self.current)

    @property
    def impact(self) -> float:
        """Impacto de fechar o gap = tamanho do gap ponderado pela importância."""
        return self.gap * self.weight

    @property
    def priority(self) -> float:
        """Quick win score = impacto / esforço (maior = fazer antes)."""
        return self.impact / self.effort if self.effort else 0.0


# ---------------------------------------------------------------------------
# Org de exemplo — perfil típico de time saindo de CI/CD tradicional
# ---------------------------------------------------------------------------

DIMENSIONS = [
    Dimension(
        name="Risco pré-deploy", tool="Harness Continuous Verification",
        weight=0.25, current=Level.INICIAL, target=Level.GERENCIADO,
        ladder=[
            "Sem verificação; deploy e torcer",
            "Dashboards olhados manualmente após deploy",
            "Alguns checks automáticos, thresholds fixos",
            "Continuous Verification com baseline + auto-rollback",
            "Verificação preditiva com risk score e policies",
        ],
        next_action="Ligar verificação automática de métricas pós-deploy com auto-rollback",
        effort=3,
    ),
    Dimension(
        name="Progressive delivery", tool="Argo Rollouts",
        weight=0.20, current=Level.AUSENTE, target=Level.GERENCIADO,
        ladder=[
            "Deploy all-at-once (recreate/rolling simples)",
            "Blue-green manual",
            "Canary com passos fixos, promoção manual",
            "Canary com AnalysisTemplate e promoção automática",
            "Canary multi-métrica + Experiment como padrão",
        ],
        next_action="Migrar 1 serviço crítico para Rollout canary com análise automática",
        effort=4,
    ),
    Dimension(
        name="Test intelligence", tool="Buildkite Test Analytics",
        weight=0.20, current=Level.INICIAL, target=Level.OTIMIZADO,
        ladder=[
            "Só verde/vermelho do build",
            "Duração total do build registrada",
            "Reliability e slow tests visíveis",
            "Flaky detection + quarentena automática",
            "Test selection preditiva por risco de mudança",
        ],
        next_action="Enviar resultados de teste ao analytics e caçar flaky/slow tests",
        effort=2,
    ),
    Dimension(
        name="Pipeline optimization", tool="Cache + paralelismo + test selection",
        weight=0.15, current=Level.DEFINIDO, target=Level.GERENCIADO,
        ladder=[
            "Pipeline serial, sem cache",
            "Cache de dependências",
            "Paralelismo por estágio",
            "Test splitting + cache de build distribuído",
            "Execução seletiva por grafo de dependências",
        ],
        next_action="Aplicar test splitting e cache distribuído para cortar o tempo de CI",
        effort=3,
    ),
    Dimension(
        name="Feature management", tool="LaunchDarkly",
        weight=0.20, current=Level.AUSENTE, target=Level.GERENCIADO,
        ladder=[
            "Sem flags; release = deploy",
            "Flags ad-hoc por env var/config",
            "Flag service com targeting básico",
            "Rollout gradual + kill switch + segmentos",
            "Experimentação (A/B) guiada por métricas",
        ],
        next_action="Adotar um flag service e separar deploy de release com kill switch",
        effort=2,
    ),
]


def maturity_score(dims: list[Dimension]) -> float:
    """Score global 0..100 ponderado pelo peso de cada dimensão."""
    total_w = sum(d.weight for d in dims)
    weighted = sum(d.current / Level.OTIMIZADO * d.weight for d in dims)
    return weighted / total_w * 100


def bar(level: int, target: int, width: int = 4) -> str:
    """Barra visual: ■ nível atual, □ até o alvo, · acima do alvo."""
    cells = []
    for i in range(1, width + 1):
        if i <= level:
            cells.append("■")
        elif i <= target:
            cells.append("□")
        else:
            cells.append("·")
    return "".join(cells)


def run_demo() -> None:
    print("=" * 70)
    print("🧭 Scorecard de maturidade — CI/CD Inteligente")
    print("   Curso 4 — CI/CD Inteligente (encerramento)")
    print("=" * 70)

    org = "Acme Corp — plataforma de e-commerce, ~40 devs"
    print(f"\n  Organização avaliada: {org}\n")

    # --- Scorecard ---
    print("─" * 70)
    print(f"  {'Dimensão':<22} {'atual→alvo':<12} {'nível':<6} gap  ferramenta")
    print("─" * 70)
    for d in DIMENSIONS:
        print(f"  {d.name:<22} {bar(d.current, d.target):<12} "
              f"{LEVEL_LABEL[d.current].split()[0]}→{LEVEL_LABEL[d.target].split()[0]:<3} "
              f"{d.gap:>2}   {d.tool}")

    score = maturity_score(DIMENSIONS)
    print("─" * 70)
    print(f"  📊 Score global de maturidade: {score:.0f}/100")

    # --- Gaps detalhados ---
    print("\n" + "─" * 70)
    print("🔍 Gaps identificados (atual vs. alvo)")
    print("─" * 70)
    for d in DIMENSIONS:
        if d.gap:
            print(f"  • {d.name}: {LEVEL_LABEL[d.current]} → {LEVEL_LABEL[d.target]}")
            print(f"      hoje: \"{d.ladder[d.current]}\"")
            print(f"      alvo: \"{d.ladder[d.target]}\"")

    # --- Roadmap priorizado ---
    print("\n" + "=" * 70)
    print("🗺️  ROADMAP DE ADOÇÃO — priorizado por quick wins (impacto/esforço)")
    print("=" * 70)
    ranked = sorted((d for d in DIMENSIONS if d.gap), key=lambda x: x.priority, reverse=True)
    print(f"\n  {'#':<3} {'Dimensão':<22} {'impacto':>8} {'esforço':>8} {'prio':>6}")
    print(f"  {'─'*3} {'─'*22} {'─'*8} {'─'*8} {'─'*6}")
    for i, d in enumerate(ranked, 1):
        tag = "⚡ quick win" if d.priority >= 0.08 and d.effort <= 2 else ""
        print(f"  {i:<3} {d.name:<22} {d.impact:>8.2f} {d.effort:>8} {d.priority:>6.3f} {tag}")

    print("\n  Sequência recomendada:")
    for i, d in enumerate(ranked, 1):
        print(f"    {i}. {d.next_action}")
        print(f"       → {d.tool}")

    print("\n" + "=" * 70)
    print("📌 CONCLUSÃO — encerramento do Curso 4")
    print("=" * 70)
    print("""
  Adoção de CI/CD inteligente não é comprar todas as ferramentas de uma
  vez: é medir a maturidade, achar os gaps e atacar primeiro os quick
  wins (alto impacto, baixo esforço). Feature management e test
  intelligence costumam ser os primeiros passos por serem baratos e de
  alto retorno, abrindo caminho para progressive delivery e verificação
  contínua de risco.

  Ao longo do Curso 4 vimos como Harness, Argo Rollouts, LaunchDarkly e
  Buildkite materializam cada dimensão. Agora você tem um mapa para
  levar essa inteligência ao seu próprio pipeline. 🚀
    """)


if __name__ == "__main__":
    run_demo()
