"""
Vídeo 4.5 — Hands-on: Automação operacional assistida
=======================================================
EXERCÍCIO PRÁTICO — Aula 4

Construção de um fluxo reativo completo ponta a ponta:
  Alerta → Diagnóstico com IA → Guardrails → Runbook → Validação

Execute:
  python automation_lab.py
"""

from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from video_4_1_respostas_automatizadas.self_healing_engine import (
    SelfHealingEngine, AlertTrigger,
)
from video_4_2_runbooks.runbook_executor import (
    create_auth_service_recovery_runbook,
)
from video_4_4_guardrails.guardrail_engine import (
    GuardrailEngine, AutomationRequest,
)


def run_lab() -> None:
    print("=" * 65)
    print("🧪 LABORATÓRIO: Automação Operacional Assistida")
    print("   Nível 1 — AIOps & Automação de Incidentes")
    print("=" * 65)

    t0 = datetime.now()

    # ------------------------------------------------------------------
    # ETAPA 1: Alerta recebido
    # ------------------------------------------------------------------
    print(f"\n{'─'*65}")
    print("ETAPA 1/5 — Alerta recebido do sistema de monitoramento")
    print(f"{'─'*65}")
    trigger = AlertTrigger(
        alert_id="ALT-2024-0001",
        service="database",
        condition="connection_pool_exhausted",
        current_value=98.0,
        threshold=90.0,
        severity="CRITICAL",
    )
    print(f"\n  🚨 Alerta: {trigger.alert_id}")
    print(f"     Serviço  : {trigger.service}")
    print(f"     Condição : {trigger.condition} = {trigger.current_value}%")
    time.sleep(0.5)

    # ------------------------------------------------------------------
    # ETAPA 2: Motor de self-healing identifica ação
    # ------------------------------------------------------------------
    print(f"\n{'─'*65}")
    print("ETAPA 2/5 — Motor de self-healing diagnostica e planeja ação")
    print(f"{'─'*65}")
    engine = SelfHealingEngine(human_in_the_loop=False)  # guardrails separados
    # Diagnóstico apenas (sem executar)
    from video_4_1_respostas_automatizadas.self_healing_engine import REMEDIATION_RULES
    planned_action = None
    for condition, service, action in REMEDIATION_RULES:
        if condition in trigger.condition and service == trigger.service:
            planned_action = action
            break

    if planned_action:
        print(f"\n  📋 Ação planejada: {planned_action.action_type.value}")
        print(f"     Risco estimado  : {planned_action.estimated_risk}")
        print(f"     Parâmetros      : {planned_action.parameters}")
    time.sleep(0.5)

    # ------------------------------------------------------------------
    # ETAPA 3: Guardrails validam a ação
    # ------------------------------------------------------------------
    print(f"\n{'─'*65}")
    print("ETAPA 3/5 — Guardrails avaliam segurança da automação")
    print(f"{'─'*65}")
    guardrail_engine = GuardrailEngine()
    automation_request = AutomationRequest(
        request_id="AUTO-001",
        action=planned_action.action_type.value if planned_action else "unknown",
        target_service="database",
        target_environment="prod",
        estimated_blast_radius=0,
        is_reversible=True,
        risk_level="LOW",
        requested_by="self-healing-engine",
        description="Aumentar max_connections temporariamente para 200",
    )
    status, checks = guardrail_engine.evaluate(automation_request)
    for check in checks:
        icon = "✅" if check.passed else "❌"
        print(f"\n  {icon} {check.message}")

    approved = status.value != "BLOCKED"
    time.sleep(0.5)

    if not approved:
        print("\n  🚫 Guardrails bloquearam a automação. Escalando para oncall.")
        return

    # ------------------------------------------------------------------
    # ETAPA 4: Executa o runbook
    # ------------------------------------------------------------------
    print(f"\n{'─'*65}")
    print("ETAPA 4/5 — Executando runbook de recuperação")
    print(f"{'─'*65}")
    runbook = create_auth_service_recovery_runbook()
    success = runbook.execute()
    time.sleep(0.3)

    # ------------------------------------------------------------------
    # ETAPA 5: Validação e encerramento
    # ------------------------------------------------------------------
    print(f"\n{'─'*65}")
    print("ETAPA 5/5 — Validação e encerramento do incidente")
    print(f"{'─'*65}")

    total_duration = (datetime.now() - t0).total_seconds()

    if success:
        print(f"""
  ✅ INCIDENTE RESOLVIDO AUTOMATICAMENTE

  Sumário:
  ─────────────────────────────────────────────
  Alerta recebido    : {t0.strftime('%H:%M:%S')}
  Resolução          : {datetime.now().strftime('%H:%M:%S')}
  Duração total      : {total_duration:.1f} segundos
  Etapas executadas  : {len(runbook.results)}
  Aprovação humana   : não necessária (risco LOW)

  Ações realizadas:
  ─────────────────────────────────────────────""")
        for r in runbook.results:
            icon = "✅" if r.status.value == "SUCCESS" else "❌"
            print(f"  {icon} {r.step_name}")
    else:
        print(f"\n  ❌ Automação falhou. Incidente escalado para oncall manual.")

    print("\n" + "=" * 65)
    print("🎓 FIM DO HANDS-ON — AULA 4 CONCLUÍDA!")
    print("=" * 65)
    print("""
  Você aprendeu a:
  ✔ Construir um motor de self-healing com máquina de estados
  ✔ Codificar runbooks operacionais como código
  ✔ Integrar IA para comunicação e geração de resumos
  ✔ Implementar guardrails e human-in-the-loop
  ✔ Orquestrar o fluxo completo de remediação automática

  Próxima aula: Operações resilientes em ambientes distribuídos →
    """)


if __name__ == "__main__":
    run_lab()
