"""
Vídeo 1.1 — Por que deploys falham? Anatomia do risco
======================================================
Gera um histórico sintético de ~200 deploys e mostra que falhas
não são aleatórias: elas se concentram em fatores mensuráveis.

Conceitos demonstrados:
- Taxa de falha global (baseline) vs. taxa condicionada a cada fator
- Fatores de risco: migration, sexta à noite, autor júnior, PR grande
- "Lift": quanto cada fator multiplica o risco em relação ao baseline
- Semente do conceito de deploy risk score (agregação de fatores)
"""

import random
from dataclasses import dataclass

random.seed(42)


@dataclass
class Deploy:
    """Um deploy do histórico, com suas features e o desfecho."""
    id: int
    arquivos_alterados: int
    linhas_adicionadas: int
    hora_do_dia: int          # 0-23
    tem_migration: bool
    testes_passaram: bool
    experiencia_autor: int    # anos de experiência (proxy de senioridade)
    sexta_feira: bool
    falhou: bool = False


def _prob_falha(d: Deploy) -> float:
    """
    Probabilidade "verdadeira" de falha usada só para SIMULAR o histórico.
    No mundo real não temos essa fórmula — é justamente o que o modelo
    dos próximos vídeos tenta aprender a partir dos dados.
    """
    p = 0.06  # risco de fundo
    if d.tem_migration:
        p += 0.22
    if d.sexta_feira and d.hora_do_dia >= 17:
        p += 0.18
    if not d.testes_passaram:
        p += 0.35
    if d.experiencia_autor <= 1:
        p += 0.12
    if d.arquivos_alterados > 25:
        p += 0.10
    if d.linhas_adicionadas > 500:
        p += 0.08
    return min(p, 0.97)


def gerar_historico(n: int = 200) -> list[Deploy]:
    """Cria um histórico realista de deploys com desfechos correlacionados."""
    deploys: list[Deploy] = []
    for i in range(n):
        d = Deploy(
            id=i + 1,
            arquivos_alterados=random.randint(1, 45),
            linhas_adicionadas=random.randint(5, 900),
            hora_do_dia=random.randint(8, 22),
            tem_migration=random.random() < 0.30,
            testes_passaram=random.random() < 0.88,
            experiencia_autor=random.randint(0, 12),
            sexta_feira=random.random() < 0.20,
        )
        d.falhou = random.random() < _prob_falha(d)
        deploys.append(d)
    return deploys


def taxa(deploys: list[Deploy]) -> float:
    """Taxa de falha (fração) de um conjunto de deploys."""
    if not deploys:
        return 0.0
    return sum(d.falhou for d in deploys) / len(deploys)


def linha_fator(nome: str, subset: list[Deploy], baseline: float) -> str:
    """Formata uma linha da tabela de fatores com taxa, contagem e lift."""
    t = taxa(subset)
    lift = (t / baseline) if baseline > 0 else 0.0
    barra = "█" * round(t * 30)
    return (
        f"  {nome:<32} {t*100:5.1f}%  (n={len(subset):>3})  "
        f"lift {lift:4.1f}x  {barra}"
    )


def analisar(deploys: list[Deploy]) -> None:
    print("=" * 70)
    print("📉 Anatomia do risco: por que deploys falham?")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)

    baseline = taxa(deploys)
    falhas = sum(d.falhou for d in deploys)

    print(f"\n  Histórico analisado:  {len(deploys)} deploys")
    print(f"  Falhas registradas:   {falhas}")
    print(f"  📊 Taxa de falha GLOBAL (baseline): {baseline*100:.1f}%")

    print("\n" + "─" * 70)
    print("🔎 Taxa de falha POR FATOR DE RISCO")
    print("─" * 70)
    print("  Se falhas fossem aleatórias, toda linha ficaria perto do baseline.\n")

    fatores = [
        ("Testes NÃO passaram",        [d for d in deploys if not d.testes_passaram]),
        ("Com migration",             [d for d in deploys if d.tem_migration]),
        ("Sexta à noite (>=17h)",     [d for d in deploys if d.sexta_feira and d.hora_do_dia >= 17]),
        ("Autor júnior (<=1 ano)",    [d for d in deploys if d.experiencia_autor <= 1]),
        ("PR grande (>25 arquivos)",  [d for d in deploys if d.arquivos_alterados > 25]),
        ("Muitas linhas (>500)",      [d for d in deploys if d.linhas_adicionadas > 500]),
    ]
    for nome, subset in sorted(fatores, key=lambda f: taxa(f[1]), reverse=True):
        print(linha_fator(nome, subset, baseline))

    # --- Combinação de fatores: o "empilhamento" de risco ---
    print("\n" + "─" * 70)
    print("⚠️  Fatores se ACUMULAM (o risco não é aditivo simples)")
    print("─" * 70)
    combo = [
        d for d in deploys
        if d.tem_migration and d.sexta_feira and d.hora_do_dia >= 17
    ]
    print(linha_fator("Migration + sexta à noite", combo, baseline))
    seguros = [
        d for d in deploys
        if d.testes_passaram and not d.tem_migration and d.experiencia_autor >= 3
    ]
    print(linha_fator("Testes OK + sem migration + sênior", seguros, baseline))

    # --- Semente do risk score ---
    print("\n" + "=" * 70)
    print("💡 A INTUIÇÃO DO DEPLOY RISK SCORE")
    print("=" * 70)
    print("""
  Cada fator empurra a probabilidade de falha para cima ou para baixo.
  E se somássemos todos eles em UM número por deploy — um "risk score"?

  Um deploy sexta à noite, com migration, testes vermelhos e autor júnior
  não é "um pouco" mais arriscado: ele acumula vários fatores de uma vez.

  Nos próximos vídeos vamos parar de olhar fator a fator na mão e deixar
  um MODELO aprender esses pesos a partir do histórico — e transformar
  isso em um score de 0 a 100 que barra o deploy antes da produção.

  ➡️  Próximo vídeo (1.2): quais FEATURES extrair de cada PR para o modelo.
    """)


if __name__ == "__main__":
    analisar(gerar_historico(200))
