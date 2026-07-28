"""
Vídeo 2.4 — Rollback inteligente: detectar degradação e reverter sozinho
=========================================================================
Durante um rollout canário, monitora as métricas em janelas curtas.
Quando o canary fica pior que o baseline por N janelas seguidas,
dispara rollback automático — sem esperar um humano perceber.

Ao final, compara o rollback automático com o rollback manual em duas
dimensões: tempo de detecção e blast radius (usuários impactados).

Conceitos demonstrados:
- Monitoramento por janelas deslizantes durante o rollout
- Regra de N janelas consecutivas ruins (evita disparo por 1 spike)
- Rollback automático vs manual: tempo de detecção e blast radius
- Timeline do incidente com o instante exato da reversão
"""

import random
from dataclasses import dataclass
from enum import Enum

random.seed(42)

TOTAL_USUARIOS = 100_000
JANELA_SEG = 30           # duração de cada janela de observação
N_JANELAS_RUINS = 2       # janelas ruins consecutivas para acionar rollback
ERRO_BASELINE = 0.010     # 1% de erro no stable
P95_BASELINE = 150.0      # ms
TEMPO_ROLLBACK_MANUAL_MIN = 14  # tempo típico até um humano perceber e agir


class Saude(str, Enum):
    OK = "🟢"
    SUSPEITA = "🟡"
    RUIM = "🔴"


@dataclass
class Janela:
    """Uma janela de observação do rollout."""
    idx: int
    peso_canary: int   # % de tráfego no canary neste momento
    error_rate: float
    p95: float

    @property
    def minuto(self) -> float:
        return self.idx * JANELA_SEG / 60

    def saude(self) -> Saude:
        erro_ruim = self.error_rate > ERRO_BASELINE * 2.5
        lat_ruim = self.p95 > P95_BASELINE * 1.6
        if erro_ruim and lat_ruim:
            return Saude.RUIM
        if erro_ruim or lat_ruim:
            return Saude.SUSPEITA
        return Saude.OK


# Cronograma de peso do canary por janela (degraus)
PESOS = [5, 5, 20, 20, 50, 50, 50, 80, 80, 100]


def gerar_janelas(degrada_em: int) -> list[Janela]:
    """
    Gera as janelas. A partir de 'degrada_em', a versão nova começa a
    piorar de forma crescente (bug que só aparece sob carga real).
    """
    janelas: list[Janela] = []
    for i, peso in enumerate(PESOS):
        if i < degrada_em:
            erro = random.uniform(0.008, 0.014)
            p95 = random.uniform(130, 165)
        else:
            severidade = 1 + (i - degrada_em) * 0.6
            erro = random.uniform(0.03, 0.05) * severidade
            p95 = random.uniform(240, 320) * (1 + 0.15 * (i - degrada_em))
        janelas.append(Janela(i, peso, erro, p95))
    return janelas


def monitorar(janelas: list[Janela]) -> int | None:
    """
    Percorre as janelas e devolve o índice em que o rollback automático
    dispara (N janelas ruins seguidas), ou None se nada disparou.
    """
    print(f"\n{'─' * 70}")
    print(f"  {'jan':>3} {'t':>5} {'peso':>5} {'error':>7} {'p95':>7}  saúde  ação")
    print(f"{'─' * 70}")
    ruins_seguidas = 0
    disparo = None
    for j in janelas:
        s = j.saude()
        if s in (Saude.RUIM, Saude.SUSPEITA):
            ruins_seguidas += 1
        else:
            ruins_seguidas = 0

        acao = ""
        if disparo is None and ruins_seguidas >= N_JANELAS_RUINS:
            disparo = j.idx
            acao = "🚨 ROLLBACK AUTOMÁTICO"

        print(
            f"  {j.idx:>3} {j.minuto:>4.1f}m {j.peso_canary:>4}% "
            f"{j.error_rate*100:>6.2f}% {j.p95:>6.0f}ms  {s.value}     {acao}"
        )
        if disparo is not None:
            break
    return disparo


def blast_radius(peso_percent: int) -> int:
    return round(peso_percent / 100 * TOTAL_USUARIOS)


def executar() -> None:
    print("=" * 70)
    print("🛟 Rollback inteligente: reverter antes do humano perceber")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)
    print(f"\n  Baseline (stable): erro {ERRO_BASELINE*100:.1f}%, p95 {P95_BASELINE:.0f}ms")
    print(f"  Regra: {N_JANELAS_RUINS} janelas ruins seguidas (janela = {JANELA_SEG}s) → rollback")

    degrada_em = 4  # canary começa a degradar quando chega a 50%
    janelas = gerar_janelas(degrada_em)
    disparo = monitorar(janelas)

    if disparo is None:
        print("\n  ✅ Nenhuma degradação sustentada — rollout seguiu até 100%.")
        return

    j_disparo = janelas[disparo]
    t_auto_min = j_disparo.minuto
    peso_auto = j_disparo.peso_canary

    # Rollback manual: humano só perceberia bem depois, com o canary já em peso alto
    peso_manual = 100  # a essa altura já teria promovido / estaria em 100%

    print("\n" + "=" * 70)
    print("⚔️  AUTOMÁTICO vs MANUAL")
    print("=" * 70)
    print(f"\n  {'Dimensão':<26} {'Automático':>16} {'Manual':>16}")
    print(f"  {'─'*26} {'─'*16} {'─'*16}")
    print(f"  {'Tempo até reverter':<26} {t_auto_min:>14.1f}m "
          f"{TEMPO_ROLLBACK_MANUAL_MIN:>14.0f}m")
    print(f"  {'Peso do canary na reversão':<26} {str(peso_auto)+'%':>16} "
          f"{str(peso_manual)+'%':>16}")
    print(f"  {'Blast radius (usuários)':<26} {blast_radius(peso_auto):>16,} "
          f"{blast_radius(peso_manual):>16,}")

    poupados = blast_radius(peso_manual) - blast_radius(peso_auto)
    ganho_tempo = TEMPO_ROLLBACK_MANUAL_MIN - t_auto_min

    print("\n" + "─" * 70)
    print("🕒 TIMELINE DO INCIDENTE")
    print("─" * 70)
    print(f"  00.0m  rollout inicia (canary 5%)")
    print(f"  {janelas[degrada_em].minuto:>4.1f}m  canary começa a degradar "
          f"(peso {janelas[degrada_em].peso_canary}%)")
    print(f"  {t_auto_min:>4.1f}m  🤖 rollback AUTOMÁTICO dispara "
          f"({N_JANELAS_RUINS} janelas ruins)")
    print(f"  {TEMPO_ROLLBACK_MANUAL_MIN:>4.1f}m  🧑 rollback MANUAL só aconteceria aqui "
          f"(pager → login → investigar)")

    print("\n" + "=" * 70)
    print("💡 CONCLUSÃO")
    print("=" * 70)
    print(f"""
  O rollback automático reverteu {ganho_tempo:.1f} min mais cedo e com o canary
  ainda em {peso_auto}% do tráfego. Isso poupou ~{poupados:,} usuários de
  serem servidos pela versão quebrada.

  A regra de "{N_JANELAS_RUINS} janelas ruins seguidas" evita reverter por causa de um
  único spike isolado, mas ainda reage em segundos — não em dezenas de minutos.

  ➡️  Próximo vídeo (2.5): juntar tudo num rollout canário de ponta a ponta.
    """)


if __name__ == "__main__":
    executar()
