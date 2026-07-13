"""
Vídeo 5.4 — Reduzindo carga cognitiva em operações complexas
==============================================================
Demonstra técnicas para filtrar ruídos e manter o foco do time
durante incidentes de alta pressão usando information hierarchy.

Conceitos demonstrados:
- Carga cognitiva em situações de crise (Miller's Law: 7±2)
- Information hierarchy: priorizar o que importa agora
- Incident command system adaptado para SRE
- Noise gates e progressive disclosure
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class IncidentContext:
    """Contexto completo de um incidente (tudo que está acontecendo)."""
    active_alerts: int
    open_dashboards: int
    slack_messages_per_min: int
    services_affected: int
    people_in_war_room: int
    parallel_investigations: int
    total_signals: int


@dataclass
class FocusedView:
    """Visão filtrada com apenas o essencial."""
    primary_signal: str
    hypothesis: str
    next_action: str
    owner: str
    timer_minutes: int
    noise_filtered: int


def build_crisis_scenario() -> IncidentContext:
    return IncidentContext(
        active_alerts=47,
        open_dashboards=12,
        slack_messages_per_min=35,
        services_affected=8,
        people_in_war_room=14,
        parallel_investigations=5,
        total_signals=340,
    )


def apply_noise_gate(context: IncidentContext) -> FocusedView:
    """Aplica filtros de ruído para reduzir a carga cognitiva."""
    return FocusedView(
        primary_signal="checkout-service error_rate=15% (SLO breach ativo)",
        hypothesis="Deploy v6.0.0 causou regressão no serializer",
        next_action="Verificar logs de SerializationError no último deploy",
        owner="Maria (on-call principal)",
        timer_minutes=10,
        noise_filtered=context.total_signals - 5,
    )


def run_demo() -> None:
    print("=" * 70)
    print("🧠 Demo: Reduzindo Carga Cognitiva em Operações")
    print("   Curso 3 — Observabilidade Inteligente")
    print("=" * 70)

    context = build_crisis_scenario()

    # Cenário: information overload
    print(f"\n{'─' * 70}")
    print("😵 CENÁRIO: Incidente SEV-1 em andamento")
    print(f"{'─' * 70}")
    print(f"""
  Estado atual do war room:
  ─────────────────────────────────────────────
  🔔 Alertas ativos         : {context.active_alerts}
  📊 Dashboards abertos     : {context.open_dashboards}
  💬 Mensagens Slack/min    : {context.slack_messages_per_min}
  🔴 Serviços afetados      : {context.services_affected}
  👥 Pessoas no war room    : {context.people_in_war_room}
  🔍 Investigações paralelas: {context.parallel_investigations}
  📡 Sinais de telemetria   : {context.total_signals}

  ⚠️  Lei de Miller: o cérebro humano processa 7±2 itens simultaneamente.
     O time está tentando processar {context.total_signals} sinais com
     {context.people_in_war_room} pessoas — é NOISE, não SIGNAL.
    """)

    # Técnicas de redução
    print(f"{'─' * 70}")
    print("🔧 TÉCNICAS DE REDUÇÃO DE CARGA COGNITIVA")
    print(f"{'─' * 70}")

    techniques = [
        ("1. INCIDENT COMMANDER", "Uma pessoa lidera, as outras executam",
         [
             "IC (Incident Commander): coordena e decide",
             "Comms Lead: comunica status para stakeholders",
             "Ops Lead: executa ações técnicas",
             "→ Reduz de 14 vozes para 3 papéis definidos",
         ]),
        ("2. NOISE GATE", "Filtrar sinais não-acionáveis no momento",
         [
             "Suprimir alertas de serviços não-primários",
             "Silenciar métricas de infra se o problema é de código",
             "Mute em canais Slack não relacionados ao incidente",
             f"→ Reduz de {context.active_alerts} alertas para ~5 relevantes",
         ]),
        ("3. PROGRESSIVE DISCLOSURE", "Revelar informação sob demanda",
         [
             "Nível 1: Status geral (🔴 Checkout DOWN, afetando 15%)",
             "Nível 2: Detalhes do serviço (error_rate, latency, logs)",
             "Nível 3: Traces individuais e código-fonte",
             "→ Cada pessoa vê apenas o nível que precisa",
         ]),
        ("4. HYPOTHESIS-DRIVEN", "Investigar uma hipótese por vez",
         [
             "Formular: 'Deploy v6.0.0 causou regressão'",
             "Validar: Verificar logs de erro pós-deploy",
             "Confirmar ou pivotar em 10 minutos",
             "→ Elimina investigações paralelas sem foco",
         ]),
        ("5. TIMER-BOXED ACTIONS", "Limite de tempo por ação",
         [
             "Se a hipótese não confirma em 10 min → pivotar",
             "Se mitigation não funciona em 15 min → escalar",
             "Se rollback não resolve em 5 min → declarar SEV-0",
             "→ Evita rabbit holes de investigação infinita",
         ]),
    ]

    for title, summary, details in techniques:
        print(f"\n  📌 {title}")
        print(f"     {summary}")
        for d in details:
            print(f"       • {d}")

    # Resultado
    focused = apply_noise_gate(context)

    print(f"\n{'─' * 70}")
    print("✅ RESULTADO: Visão focada após filtros")
    print(f"{'─' * 70}")
    print(f"""
  De {context.total_signals} sinais → 5 sinais relevantes
  ({focused.noise_filtered} sinais de ruído filtrados)

  🎯 FOCO AGORA:
  ─────────────────────────────────────────────
  Sinal primário  : {focused.primary_signal}
  Hipótese        : {focused.hypothesis}
  Próxima ação    : {focused.next_action}
  Responsável     : {focused.owner}
  Timer           : {focused.timer_minutes} minutos até reavaliação
    """)

    # Comparativo
    print(f"{'=' * 70}")
    print("📊 IMPACTO DA REDUÇÃO DE CARGA COGNITIVA")
    print(f"{'=' * 70}")
    print(f"""
  {'Métrica':<35} {'Sem filtros':<18} {'Com filtros':<18}
  {'─' * 35} {'─' * 18} {'─' * 18}
  {'Sinais para processar':<35} {context.total_signals:<18} {'5':<18}
  {'Pessoas decidindo':<35} {context.people_in_war_room:<18} {'3 (IC/Comms/Ops)':<18}
  {'Investigações paralelas':<35} {context.parallel_investigations:<18} {'1 (hipótese)':<18}
  {'Dashboards abertos':<35} {context.open_dashboards:<18} {'2 (overview+svc)':<18}
  {'MTTR estimado':<35} {'45-90 min':<18} {'15-25 min':<18}
    """)

    print("=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  Em crises, MENOS é MAIS. A carga cognitiva é o inimigo silencioso
  que transforma um incidente de 15 minutos em uma maratona de 2 horas.

  Framework: IC + Noise Gate + Progressive Disclosure + Hypothesis
  → Reduz MTTR em 50-70% ao eliminar paralisia por sobrecarga.

  Na Aula 5.5 (Hands-on final!), vamos simular uma crise completa
  usando todas as técnicas do curso.
    """)


if __name__ == "__main__":
    run_demo()
