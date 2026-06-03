"""
Vídeo 5.2 — Fluxos operacionais integrados
===========================================
Demonstra o pipeline unificado desde o disparo do sinal
até a resolução do incidente, sincronizando monitoramento,
comunicação e automação de chamados.

Conceitos demonstrados:
- Pipeline event-driven completo (signal → resolve)
- Integração de múltiplos sistemas (monitoring + ticketing + chat)
- SLO tracking durante o incidente
- Handoff entre sistemas automáticos e humanos
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Callable, Optional


class PipelineStage(Enum):
    SIGNAL_RECEIVED    = auto()
    ALERT_FIRED        = auto()
    CORRELATED         = auto()
    TRIAGED            = auto()
    TEAM_NOTIFIED      = auto()
    DIAGNOSIS_COMPLETE = auto()
    REMEDIATION_ACTIVE = auto()
    VALIDATING         = auto()
    RESOLVED           = auto()


@dataclass
class PipelineEvent:
    stage: PipelineStage
    timestamp: datetime
    system: str       # datadog | pagerduty | slack | jira | self-healing
    message: str
    data: dict = field(default_factory=dict)


class UnifiedOperationsPipeline:
    """
    Pipeline operacional unificado que orquestra todos os sistemas
    desde a detecção até a resolução e documentação.
    """

    def __init__(self, incident_id: str):
        self.incident_id = incident_id
        self.events: list[PipelineEvent] = []
        self.current_stage = PipelineStage.SIGNAL_RECEIVED
        self.slo_burn_events: list[tuple[datetime, float]] = []
        self.start_time = datetime.now()

    def _log_event(self, stage: PipelineStage, system: str, message: str, data: dict = {}) -> None:
        event = PipelineEvent(stage, datetime.now(), system, message, data)
        self.events.append(event)
        elapsed = (event.timestamp - self.start_time).total_seconds()
        print(f"  [{elapsed:>5.1f}s] [{system:<15}] {message}")
        self.current_stage = stage

    def run(self) -> None:
        """Executa o pipeline completo de resposta a incidente."""
        print(f"\n{'='*65}")
        print(f"  🚀 PIPELINE OPERACIONAL — {self.incident_id}")
        print(f"{'='*65}\n")

        # ETAPA 1: Sinal detectado pelo Datadog
        self._log_event(PipelineStage.SIGNAL_RECEIVED, "datadog",
            "Watchdog: anomalia detectada em auth-service.error_rate",
            {"value": 0.89, "baseline": 0.02})
        time.sleep(0.15)

        # ETAPA 2: Alerta disparado
        self._log_event(PipelineStage.ALERT_FIRED, "datadog",
            "Monitor #12001 fired: auth-service error rate CRITICAL (89%)")
        time.sleep(0.1)

        # ETAPA 3: Correlação automática de alertas
        self._log_event(PipelineStage.CORRELATED, "datadog",
            "Correlate Alerts: 9 alertas agrupados em 1 incidente",
            {"grouped": 9, "root_service": "auth-service"})
        time.sleep(0.1)

        # ETAPA 4: Triagem com impact score
        self._log_event(PipelineStage.TRIAGED, "self-healing",
            "Impact Score: 87/100 → P1 | Blast radius: 50.000 usuários")
        time.sleep(0.1)

        # ETAPA 5: Notificação do time via PagerDuty + Slack
        self._log_event(PipelineStage.TEAM_NOTIFIED, "pagerduty",
            "Oncall engineer notificado: alice@company.com (response: 2min)")
        time.sleep(0.15)
        self._log_event(PipelineStage.TEAM_NOTIFIED, "slack",
            "War room criada: #inc-2024-0603-001 | Summary enviado")
        time.sleep(0.1)

        # ETAPA 6: Ticket criado no Jira/ServiceNow
        self._log_event(PipelineStage.TEAM_NOTIFIED, "jira",
            "Incident ticket criado: INC-2024-0603-001 (P1)")
        time.sleep(0.1)

        # ETAPA 7: Diagnóstico com IA
        self._log_event(PipelineStage.DIAGNOSIS_COMPLETE, "llm-assistant",
            "Root Cause: Deploy CHG-001 (auth-service v2.3.1) | Confiança: 87%")
        time.sleep(0.15)

        # ETAPA 8: Guardrails validam ação
        self._log_event(PipelineStage.REMEDIATION_ACTIVE, "guardrail-engine",
            "Guardrails: PASSED (risco LOW, blast=0, reversível) → AUTO-APPROVED")
        time.sleep(0.1)

        # ETAPA 9: Runbook executado
        self._log_event(PipelineStage.REMEDIATION_ACTIVE, "runbook-executor",
            "Runbook: auth-service-connection-pool-recovery STARTED (6 steps)")
        time.sleep(0.3)
        self._log_event(PipelineStage.REMEDIATION_ACTIVE, "runbook-executor",
            "Runbook COMPLETED: max_connections=200, rolling restart OK")
        time.sleep(0.1)

        # ETAPA 10: Validação
        self._log_event(PipelineStage.VALIDATING, "datadog",
            "Validação: error_rate = 0.008 (0.8%) → abaixo do threshold ✅")
        time.sleep(0.1)

        # ETAPA 11: Resolução
        self._log_event(PipelineStage.RESOLVED, "pagerduty",
            "Incidente resolvido | MTTR: 18 min | SLO burn: 0.02%")
        time.sleep(0.1)
        self._log_event(PipelineStage.RESOLVED, "slack",
            "War room: Resolução notificada | Post-mortem agendado")
        time.sleep(0.1)
        self._log_event(PipelineStage.RESOLVED, "jira",
            "Ticket INC-2024-0603-001: RESOLVED | RCA draft anexado")

        self._print_summary()

    def _print_summary(self) -> None:
        total_elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"\n{'─'*65}")
        print(f"  📊 RESUMO DO PIPELINE")
        print(f"{'─'*65}")
        print(f"""
  Incidente ID    : {self.incident_id}
  Duração total   : {total_elapsed:.1f}s (simulação)
  Eventos gerados : {len(self.events)}
  Sistemas envolvidos: datadog, pagerduty, slack, jira, llm, runbook

  Estágios percorridos:
  {" → ".join(e.stage.name for e in self.events if e.stage != self.events[self.events.index(e)-1].stage or self.events.index(e) == 0)}

  Automação vs. Humano:
  • Auto: detecção, correlação, triagem, guardrails, runbook, validação
  • Humano: war room oversight, post-mortem review, action items
        """)


if __name__ == "__main__":
    print("🔬 Demo: Fluxos Operacionais Integrados")
    print("     Nível 1 — AIOps & Automação de Incidentes")

    pipeline = UnifiedOperationsPipeline("INC-2024-0603-001")
    pipeline.run()
