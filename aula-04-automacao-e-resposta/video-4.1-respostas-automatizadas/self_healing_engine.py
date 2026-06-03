"""
Vídeo 4.1 — Automatizando respostas operacionais
=================================================
Demonstra o ciclo de autorremediação nas plataformas modernas
de AIOps: detecção → diagnóstico → ação → validação.

Conceitos demonstrados:
- Event-driven remediation (gatilhos de observabilidade)
- Máquina de estados de um ciclo de self-healing
- Padrões de ação: restart, scale, rollback, throttle
- Integração com sistemas externos (Kubernetes, Datadog)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Callable, Optional


class RemediationState(Enum):
    IDLE        = auto()
    TRIGGERED   = auto()
    DIAGNOSING  = auto()
    PLANNING    = auto()
    AWAITING_APPROVAL = auto()
    EXECUTING   = auto()
    VALIDATING  = auto()
    RESOLVED    = auto()
    FAILED      = auto()
    ESCALATED   = auto()


class ActionType(Enum):
    RESTART_SERVICE   = "restart_service"
    SCALE_UP          = "scale_up"
    ROLLBACK_DEPLOY   = "rollback_deploy"
    CLEAR_CACHE       = "clear_cache"
    INCREASE_POOL     = "increase_connection_pool"
    THROTTLE_TRAFFIC  = "throttle_traffic"
    NOTIFY_ONCALL     = "notify_oncall"


@dataclass
class RemediationAction:
    """Define uma ação de remediação com seus parâmetros."""
    action_type: ActionType
    target_service: str
    parameters: dict = field(default_factory=dict)
    requires_approval: bool = False
    estimated_risk: str = "LOW"   # LOW | MEDIUM | HIGH
    estimated_duration_sec: int = 30


@dataclass
class AlertTrigger:
    """Gatilho que inicia o ciclo de remediação."""
    alert_id: str
    service: str
    condition: str
    current_value: float
    threshold: float
    severity: str
    fired_at: datetime = field(default_factory=datetime.now)


@dataclass
class RemediationResult:
    """Resultado de uma execução de remediação."""
    action: RemediationAction
    success: bool
    output: str
    duration_sec: float
    timestamp: datetime = field(default_factory=datetime.now)


# ---------------------------------------------------------------------------
# Regras de remediação (trigger → ação)
# ---------------------------------------------------------------------------

REMEDIATION_RULES: list[tuple[str, str, RemediationAction]] = [
    # (condição_regex, serviço_alvo, ação)
    ("connection_pool_exhausted", "database",
     RemediationAction(
         ActionType.INCREASE_POOL, "database",
         {"new_max_connections": 200}, requires_approval=False,
         estimated_risk="LOW", estimated_duration_sec=5,
     )),
    ("high_error_rate", "auth-service",
     RemediationAction(
         ActionType.RESTART_SERVICE, "auth-service",
         {"pods": 3, "strategy": "rolling"}, requires_approval=False,
         estimated_risk="MEDIUM", estimated_duration_sec=60,
     )),
    ("high_error_rate", "payment-service",
     RemediationAction(
         ActionType.ROLLBACK_DEPLOY, "payment-service",
         {"target_version": "previous"}, requires_approval=True,
         estimated_risk="HIGH", estimated_duration_sec=120,
     )),
    ("memory_pressure", "*",
     RemediationAction(
         ActionType.SCALE_UP, "affected_service",
         {"replicas_delta": 2}, requires_approval=False,
         estimated_risk="LOW", estimated_duration_sec=45,
     )),
]


# ---------------------------------------------------------------------------
# Motor de self-healing
# ---------------------------------------------------------------------------

class SelfHealingEngine:
    """
    Motor de autorremediação baseado em máquina de estados.
    Implementa o ciclo: trigger → diagnose → plan → [approve] → execute → validate
    """

    def __init__(self, human_in_the_loop: bool = True):
        self.state = RemediationState.IDLE
        self.human_in_the_loop = human_in_the_loop
        self._history: list[RemediationResult] = []
        self._current_trigger: Optional[AlertTrigger] = None

    def _transition(self, new_state: RemediationState) -> None:
        print(f"    [STATE] {self.state.name} → {new_state.name}")
        self.state = new_state

    def handle_alert(self, trigger: AlertTrigger) -> Optional[RemediationResult]:
        """Pipeline completo de remediação a partir de um alerta."""
        self._current_trigger = trigger
        self._transition(RemediationState.TRIGGERED)

        print(f"\n  🚨 Alerta recebido: {trigger.alert_id}")
        print(f"     Serviço  : {trigger.service}")
        print(f"     Condição : {trigger.condition} = {trigger.current_value:.2f} (threshold: {trigger.threshold})")

        # 1. Diagnose
        self._transition(RemediationState.DIAGNOSING)
        action = self._find_remediation(trigger)
        if not action:
            print(f"  ⚠️  Nenhuma regra de remediação encontrada. Escalando...")
            self._transition(RemediationState.ESCALATED)
            return None

        # 2. Plan
        self._transition(RemediationState.PLANNING)
        print(f"\n  📋 Plano de remediação:")
        print(f"     Ação     : {action.action_type.value}")
        print(f"     Alvo     : {action.target_service}")
        print(f"     Risco    : {action.estimated_risk}")
        print(f"     Parâmetros: {action.parameters}")

        # 3. Aprovação (guardrail)
        if action.requires_approval or self.human_in_the_loop:
            self._transition(RemediationState.AWAITING_APPROVAL)
            approved = self._request_approval(action)
            if not approved:
                print(f"  ❌ Aprovação negada. Escalando para oncall.")
                self._transition(RemediationState.ESCALATED)
                return None

        # 4. Execute
        self._transition(RemediationState.EXECUTING)
        result = self._execute_action(action)
        self._history.append(result)

        # 5. Validate
        self._transition(RemediationState.VALIDATING)
        if result.success:
            time.sleep(0.2)
            print(f"  ✅ Validação: serviço normalizado")
            self._transition(RemediationState.RESOLVED)
        else:
            print(f"  ❌ Ação falhou. Escalando para oncall.")
            self._transition(RemediationState.FAILED)

        return result

    def _find_remediation(self, trigger: AlertTrigger) -> Optional[RemediationAction]:
        for condition, service, action in REMEDIATION_RULES:
            if condition in trigger.condition and (service == trigger.service or service == "*"):
                return action
        return None

    def _request_approval(self, action: RemediationAction) -> bool:
        """Simula o processo de aprovação humana."""
        print(f"\n  👤 HUMAN-IN-THE-LOOP: Aguardando aprovação...")
        print(f"     Ação de risco {action.estimated_risk} requer confirmação.")
        time.sleep(0.5)
        # Em ambiente real: notificaria Slack/PagerDuty e aguardaria resposta
        approved = action.estimated_risk in ("LOW", "MEDIUM")
        status = "✅ APROVADA" if approved else "❌ NEGADA"
        print(f"     Resposta: {status}")
        return approved

    def _execute_action(self, action: RemediationAction) -> RemediationResult:
        """Simula a execução de uma ação de remediação."""
        print(f"\n  ⚙️  Executando: {action.action_type.value} em {action.target_service}...")
        start = datetime.now()
        time.sleep(0.3)

        # Simula sucesso/falha
        success = action.estimated_risk != "HIGH"
        output = f"Action {action.action_type.value} completed successfully" if success else "Action failed: timeout"
        duration = (datetime.now() - start).total_seconds()

        status_icon = "✅" if success else "❌"
        print(f"  {status_icon} {output} ({duration:.1f}s)")

        return RemediationResult(action=action, success=success, output=output, duration_sec=duration)


if __name__ == "__main__":
    print("🔬 Demo: Automatizando Respostas Operacionais")
    print("     Nível 1 — AIOps & Automação de Incidentes\n")

    engine = SelfHealingEngine(human_in_the_loop=True)

    # Cenário 1: Connection pool esgotado (risco LOW, autorizado automaticamente)
    print("=" * 65)
    print("CENÁRIO 1: Connection pool esgotado (autorremediação automática)")
    print("=" * 65)
    trigger1 = AlertTrigger(
        alert_id="ALT-001", service="database",
        condition="connection_pool_exhausted",
        current_value=100.0, threshold=90.0, severity="CRITICAL",
    )
    engine.handle_alert(trigger1)

    # Cenário 2: Alta taxa de erro no payment-service (risco HIGH, requer aprovação)
    print("\n" + "=" * 65)
    print("CENÁRIO 2: Payment-service com alta taxa de erro (aprovação necessária)")
    print("=" * 65)
    engine2 = SelfHealingEngine(human_in_the_loop=True)
    trigger2 = AlertTrigger(
        alert_id="ALT-002", service="payment-service",
        condition="high_error_rate",
        current_value=1.0, threshold=0.05, severity="CRITICAL",
    )
    engine2.handle_alert(trigger2)
