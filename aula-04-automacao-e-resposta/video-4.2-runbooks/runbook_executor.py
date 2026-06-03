"""
Vídeo 4.2 — Runbooks e fluxos automatizados
============================================
Demonstra como modelar e executar runbooks operacionais como
código — codificando rotinas automáticas de reinicialização,
rollbacks e escalonamentos com fluxos lógicos claros.

Conceitos demonstrados:
- Runbook-as-Code: definição declarativa de playbooks
- Execução sequencial e paralela de etapas
- Tratamento de erros e fallbacks
- Auditoria e rastreabilidade de execuções
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Optional


class StepStatus(Enum):
    PENDING  = "PENDING"
    RUNNING  = "RUNNING"
    SUCCESS  = "SUCCESS"
    FAILED   = "FAILED"
    SKIPPED  = "SKIPPED"


@dataclass
class RunbookStep:
    """Uma etapa de um runbook."""
    name: str
    description: str
    action: Callable[[], tuple[bool, str]]  # retorna (success, output)
    on_failure: str = "abort"               # abort | continue | fallback
    timeout_sec: int = 60
    required: bool = True


@dataclass
class StepResult:
    step_name: str
    status: StepStatus
    output: str
    duration_sec: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Runbook:
    """Define um runbook operacional como código."""
    name: str
    description: str
    trigger_condition: str
    affected_service: str
    steps: list[RunbookStep] = field(default_factory=list)
    results: list[StepResult] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def execute(self) -> bool:
        """Executa o runbook step-by-step com logging completo."""
        self.started_at = datetime.now()
        self.results = []

        print(f"\n  📋 RUNBOOK: {self.name}")
        print(f"  Serviço  : {self.affected_service}")
        print(f"  Trigger  : {self.trigger_condition}")
        print(f"  Etapas   : {len(self.steps)}")
        print(f"  Início   : {self.started_at.strftime('%H:%M:%S')}")
        print(f"  {'─'*55}")

        overall_success = True

        for i, step in enumerate(self.steps, 1):
            print(f"\n  [{i}/{len(self.steps)}] {step.name}")
            print(f"         {step.description}")

            start = datetime.now()
            success, output = step.action()
            duration = (datetime.now() - start).total_seconds()

            status = StepStatus.SUCCESS if success else StepStatus.FAILED
            icon = "✅" if success else "❌"
            print(f"         {icon} {output} ({duration:.1f}s)")

            self.results.append(StepResult(
                step_name=step.name, status=status,
                output=output, duration_sec=duration,
            ))

            if not success:
                overall_success = False
                if step.on_failure == "abort":
                    print(f"  🛑 Etapa crítica falhou. Abortando runbook.")
                    break
                elif step.on_failure == "continue":
                    print(f"  ⚠️  Falha não-crítica. Continuando...")

        self.completed_at = datetime.now()
        total_duration = (self.completed_at - self.started_at).total_seconds()

        status_icon = "✅" if overall_success else "❌"
        print(f"\n  {'─'*55}")
        print(f"  {status_icon} Runbook {'CONCLUÍDO' if overall_success else 'FALHOU'} em {total_duration:.1f}s")

        return overall_success

    def audit_log(self) -> str:
        """Gera o log de auditoria da execução."""
        lines = [
            f"RUNBOOK AUDIT LOG",
            f"  Name      : {self.name}",
            f"  Service   : {self.affected_service}",
            f"  Started   : {self.started_at}",
            f"  Completed : {self.completed_at}",
            f"  Steps     : {len(self.results)}",
            "",
        ]
        for r in self.results:
            lines.append(f"  [{r.status.value:<8}] {r.step_name}: {r.output} ({r.duration_sec:.1f}s)")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Simuladores de ações operacionais reais
# ---------------------------------------------------------------------------

def simulate_action(name: str, success: bool = True, delay: float = 0.2) -> Callable:
    def action() -> tuple[bool, str]:
        time.sleep(delay)
        if success:
            return True, f"{name}: completed successfully"
        else:
            return False, f"{name}: failed with error"
    return action


# ---------------------------------------------------------------------------
# Runbooks pré-definidos
# ---------------------------------------------------------------------------

def create_auth_service_recovery_runbook() -> Runbook:
    """Runbook de recuperação do auth-service."""
    return Runbook(
        name="auth-service-connection-pool-recovery",
        description="Recuperação automática de esgotamento do connection pool",
        trigger_condition="connection_pool_exhausted (>95%)",
        affected_service="auth-service",
        steps=[
            RunbookStep(
                "check_current_connections",
                "Verifica conexões ativas no PostgreSQL",
                simulate_action("SELECT count(*) FROM pg_stat_activity"),
                on_failure="abort",
            ),
            RunbookStep(
                "identify_long_running_queries",
                "Identifica e termina queries travadas (>30s)",
                simulate_action("SELECT pg_terminate_backend(pid) WHERE duration > 30s"),
                on_failure="continue",
            ),
            RunbookStep(
                "increase_max_connections_temp",
                "Aumenta max_connections temporariamente para 200",
                simulate_action("ALTER SYSTEM SET max_connections = 200; SELECT pg_reload_conf()"),
                on_failure="abort",
            ),
            RunbookStep(
                "rolling_restart_auth_pods",
                "Rolling restart dos pods do auth-service para liberar conexões",
                simulate_action("kubectl rollout restart deployment/auth-service", delay=0.5),
                on_failure="abort",
            ),
            RunbookStep(
                "verify_service_health",
                "Aguarda e verifica saúde do serviço após restart",
                simulate_action("kubectl rollout status deployment/auth-service --timeout=120s", delay=0.3),
                on_failure="abort",
            ),
            RunbookStep(
                "validate_error_rate",
                "Confirma redução da taxa de erro (<5%)",
                simulate_action("datadog.query('auth_service.error_rate < 0.05', window=2m)"),
                on_failure="continue",
            ),
            RunbookStep(
                "notify_resolution",
                "Notifica canal de incidentes sobre resolução",
                simulate_action("slack.post('#incidents', 'auth-service recovered')"),
                on_failure="continue",
            ),
        ]
    )


def create_service_rollback_runbook() -> Runbook:
    """Runbook de rollback de deployment."""
    return Runbook(
        name="auth-service-emergency-rollback",
        description="Rollback de emergência para versão anterior estável",
        trigger_condition="error_rate > 80% after deployment",
        affected_service="auth-service",
        steps=[
            RunbookStep(
                "get_previous_revision",
                "Obtém revisão anterior do deployment",
                simulate_action("kubectl rollout history deployment/auth-service"),
                on_failure="abort",
            ),
            RunbookStep(
                "execute_rollback",
                "Executa rollback para revisão anterior",
                simulate_action("kubectl rollout undo deployment/auth-service", delay=0.5),
                on_failure="abort",
            ),
            RunbookStep(
                "wait_rollout",
                "Aguarda conclusão do rollout",
                simulate_action("kubectl rollout status deployment/auth-service", delay=0.4),
                on_failure="abort",
            ),
            RunbookStep(
                "smoke_test",
                "Executa smoke test no auth endpoint",
                simulate_action("curl -f https://api.prod/health/auth"),
                on_failure="abort",
            ),
            RunbookStep(
                "create_incident_ticket",
                "Cria ticket de incidente com contexto do rollback",
                simulate_action("jira.create_issue(type=INCIDENT, priority=P1)"),
                on_failure="continue",
            ),
        ]
    )


if __name__ == "__main__":
    print("🔬 Demo: Runbooks e Fluxos Automatizados")
    print("     Nível 1 — AIOps & Automação de Incidentes")

    print("\n" + "=" * 65)
    print("RUNBOOK 1: Recuperação de Connection Pool")
    print("=" * 65)
    runbook1 = create_auth_service_recovery_runbook()
    success1 = runbook1.execute()

    print("\n" + "─" * 65)
    print("AUDIT LOG:")
    print("─" * 65)
    print(runbook1.audit_log())

    print("\n" + "=" * 65)
    print("RUNBOOK 2: Rollback de Emergência")
    print("=" * 65)
    runbook2 = create_service_rollback_runbook()
    runbook2.execute()
