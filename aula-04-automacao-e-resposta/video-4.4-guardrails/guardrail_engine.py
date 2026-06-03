"""
Vídeo 4.4 — Guardrails e aprovação humana
==========================================
Demonstra como implementar travas de segurança e cenários de
human-in-the-loop para conter o raio de impacto de automações.

Conceitos demonstrados:
- Guardrails baseados em risco e contexto
- Circuit breaker para automações
- Blast radius estimation (quantos usuários serão afetados)
- Aprovação hierárquica (auto-approve → team lead → director)
- Audit trail completo de automações
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class ApprovalLevel(Enum):
    AUTO_APPROVED  = "AUTO_APPROVED"  # nenhuma aprovação necessária
    TEAM_APPROVAL  = "TEAM_APPROVAL"  # time de plantão
    LEAD_APPROVAL  = "LEAD_APPROVAL"  # tech lead / SRE lead
    DIRECTOR_APPROVAL = "DIRECTOR"   # diretor / CTO


class GuardrailStatus(Enum):
    PASSED  = "PASSED"
    BLOCKED = "BLOCKED"
    PENDING = "PENDING"


@dataclass
class AutomationRequest:
    """Solicitação de execução de uma automação."""
    request_id: str
    action: str
    target_service: str
    target_environment: str   # prod | staging | dev
    estimated_blast_radius: int  # usuários afetados estimados
    is_reversible: bool
    risk_level: str           # LOW | MEDIUM | HIGH | CRITICAL
    requested_by: str         # "system" ou nome do usuário
    description: str
    parameters: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class GuardrailCheck:
    """Resultado de uma checagem de guardrail."""
    check_name: str
    passed: bool
    message: str
    blocks_execution: bool = True


@dataclass
class ApprovalDecision:
    """Decisão de aprovação de uma automação."""
    request_id: str
    level: ApprovalLevel
    approved: bool
    approver: str
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AutomationAuditEntry:
    """Entrada de auditoria de uma automação."""
    request: AutomationRequest
    guardrails: list[GuardrailCheck]
    approvals: list[ApprovalDecision]
    executed: bool
    outcome: str
    timestamp: datetime = field(default_factory=datetime.now)


# ---------------------------------------------------------------------------
# Motor de guardrails
# ---------------------------------------------------------------------------

class GuardrailEngine:
    """
    Motor de guardrails para automações operacionais.

    Implementa múltiplas camadas de proteção antes de executar
    qualquer ação automatizada em produção.
    """

    def __init__(self):
        self._circuit_breaker_failures: dict[str, int] = {}
        self._circuit_breaker_window = timedelta(hours=1)
        self._circuit_breaker_threshold = 3
        self._audit_log: list[AutomationAuditEntry] = []

    def evaluate(self, request: AutomationRequest) -> tuple[GuardrailStatus, list[GuardrailCheck]]:
        """Avalia todos os guardrails para uma solicitação de automação."""
        checks: list[GuardrailCheck] = []

        # GUARDRAIL 1: Ambiente de produção requer aprovação mínima
        if request.target_environment == "prod":
            prod_check = GuardrailCheck(
                "prod_environment_check",
                passed=request.risk_level in ("LOW",),
                message=(
                    "✅ Ação de baixo risco em produção — permitida"
                    if request.risk_level == "LOW"
                    else f"❌ Ação de risco {request.risk_level} em PROD requer aprovação humana"
                ),
                blocks_execution=request.risk_level not in ("LOW",),
            )
            checks.append(prod_check)

        # GUARDRAIL 2: Blast radius máximo para auto-aprovação
        blast_limit = 1000  # usuários
        blast_check = GuardrailCheck(
            "blast_radius_check",
            passed=request.estimated_blast_radius <= blast_limit,
            message=(
                f"✅ Blast radius aceitável ({request.estimated_blast_radius} usuários)"
                if request.estimated_blast_radius <= blast_limit
                else f"❌ Blast radius muito alto ({request.estimated_blast_radius} > {blast_limit} usuários)"
            ),
            blocks_execution=request.estimated_blast_radius > blast_limit,
        )
        checks.append(blast_check)

        # GUARDRAIL 3: Ações irreversíveis precisam de aprovação explícita
        reversible_check = GuardrailCheck(
            "reversibility_check",
            passed=request.is_reversible,
            message=(
                "✅ Ação reversível — rollback disponível"
                if request.is_reversible
                else "❌ Ação IRREVERSÍVEL — aprovação manual obrigatória"
            ),
            blocks_execution=not request.is_reversible,
        )
        checks.append(reversible_check)

        # GUARDRAIL 4: Circuit breaker — muitas falhas recentes no serviço
        failures = self._circuit_breaker_failures.get(request.target_service, 0)
        circuit_check = GuardrailCheck(
            "circuit_breaker_check",
            passed=failures < self._circuit_breaker_threshold,
            message=(
                f"✅ Circuit breaker fechado ({failures} falhas recentes)"
                if failures < self._circuit_breaker_threshold
                else f"❌ Circuit breaker ABERTO — {failures} falhas no {request.target_service} (1h)"
            ),
            blocks_execution=failures >= self._circuit_breaker_threshold,
        )
        checks.append(circuit_check)

        # GUARDRAIL 5: Rate limiting — não executar a mesma ação muito frequentemente
        rate_check = GuardrailCheck(
            "rate_limit_check",
            passed=True,  # simplificado para demo
            message="✅ Dentro do limite de frequência de automações",
            blocks_execution=False,
        )
        checks.append(rate_check)

        # Determina status geral
        blocked_checks = [c for c in checks if not c.passed and c.blocks_execution]
        if blocked_checks:
            return GuardrailStatus.BLOCKED, checks
        elif any(not c.passed for c in checks):
            return GuardrailStatus.PENDING, checks
        else:
            return GuardrailStatus.PASSED, checks

    def determine_approval_level(self, request: AutomationRequest) -> ApprovalLevel:
        """Determina o nível de aprovação necessário."""
        if request.risk_level == "CRITICAL" or not request.is_reversible:
            return ApprovalLevel.DIRECTOR_APPROVAL
        elif request.risk_level == "HIGH" or request.estimated_blast_radius > 5000:
            return ApprovalLevel.LEAD_APPROVAL
        elif request.risk_level == "MEDIUM" or request.target_environment == "prod":
            return ApprovalLevel.TEAM_APPROVAL
        else:
            return ApprovalLevel.AUTO_APPROVED

    def simulate_approval(
        self,
        request: AutomationRequest,
        level: ApprovalLevel,
    ) -> ApprovalDecision:
        """Simula o processo de aprovação (em prod: Slack bot / PagerDuty)."""
        print(f"\n  👤 Aprovação requerida: {level.value}")
        time.sleep(0.3)

        # Lógica de aprovação simulada
        if level == ApprovalLevel.AUTO_APPROVED:
            return ApprovalDecision(request.request_id, level, True, "system", "Auto-approved: low risk")
        elif level == ApprovalLevel.TEAM_APPROVAL:
            print(f"     → Notificando #oncall-team via Slack...")
            time.sleep(0.3)
            return ApprovalDecision(request.request_id, level, True, "oncall-engineer", "Approved: context reviewed")
        elif level == ApprovalLevel.LEAD_APPROVAL:
            print(f"     → Notificando Tech Lead via PagerDuty...")
            time.sleep(0.4)
            return ApprovalDecision(request.request_id, level, True, "tech-lead", "Approved with monitoring")
        else:  # DIRECTOR
            print(f"     → Escalando para Director — aguardando resposta manual...")
            time.sleep(0.5)
            return ApprovalDecision(request.request_id, level, False, "system",
                                    "TIMEOUT: Director not reachable — auto-blocked for safety")

    def process_request(self, request: AutomationRequest) -> bool:
        """Processa uma solicitação de automação com todos os guardrails."""
        print(f"\n  {'='*55}")
        print(f"  🛡️  GUARDRAILS — {request.request_id}")
        print(f"  Ação     : {request.action}")
        print(f"  Alvo     : {request.target_service} ({request.target_environment})")
        print(f"  Risco    : {request.risk_level}")
        print(f"  Blast    : {request.estimated_blast_radius:,} usuários")
        print(f"  {'─'*55}")

        # Avalia guardrails
        status, checks = self.evaluate(request)
        for check in checks:
            icon = "✅" if check.passed else ("❌" if check.blocks_execution else "⚠️ ")
            print(f"  {icon} [{check.check_name}]: {check.message}")

        if status == GuardrailStatus.BLOCKED:
            print(f"\n  🚫 AUTOMAÇÃO BLOQUEADA pelos guardrails acima.")
            self._audit_log.append(AutomationAuditEntry(
                request=request, guardrails=checks, approvals=[],
                executed=False, outcome="BLOCKED_BY_GUARDRAIL",
            ))
            return False

        # Aprovação
        level = self.determine_approval_level(request)
        approval = self.simulate_approval(request, level)

        if not approval.approved:
            print(f"\n  🚫 AUTOMAÇÃO BLOQUEADA: aprovação negada por {approval.approver}")
            self._audit_log.append(AutomationAuditEntry(
                request=request, guardrails=checks, approvals=[approval],
                executed=False, outcome="APPROVAL_DENIED",
            ))
            return False

        # Execução autorizada
        print(f"\n  ✅ Aprovado por {approval.approver} — executando automação...")
        time.sleep(0.3)
        print(f"  ✅ Automação executada com sucesso.")

        self._audit_log.append(AutomationAuditEntry(
            request=request, guardrails=checks, approvals=[approval],
            executed=True, outcome="SUCCESS",
        ))
        return True


if __name__ == "__main__":
    print("🔬 Demo: Guardrails e Aprovação Humana")
    print("     Nível 1 — AIOps & Automação de Incidentes")

    engine = GuardrailEngine()

    # Cenário 1: Ação de baixo risco — aprovação automática
    print("\n" + "=" * 65)
    print("CENÁRIO 1: Limpar cache Redis (baixo risco, auto-aprovado)")
    print("=" * 65)
    engine.process_request(AutomationRequest(
        "REQ-001", "clear_cache", "redis-cluster", "prod",
        estimated_blast_radius=0, is_reversible=True, risk_level="LOW",
        requested_by="system", description="Cache clear após deploy de produto",
    ))

    # Cenário 2: Rollback em prod — aprovação do team lead
    print("\n" + "=" * 65)
    print("CENÁRIO 2: Rollback do auth-service (risco HIGH)")
    print("=" * 65)
    engine.process_request(AutomationRequest(
        "REQ-002", "rollback_deploy", "auth-service", "prod",
        estimated_blast_radius=50_000, is_reversible=True, risk_level="HIGH",
        requested_by="system", description="Rollback auth-service v2.3.1 → v2.3.0",
    ))

    # Cenário 3: Drop de tabela — bloqueado por ser irreversível
    print("\n" + "=" * 65)
    print("CENÁRIO 3: Drop de tabela legada (IRREVERSÍVEL — deve bloquear)")
    print("=" * 65)
    engine.process_request(AutomationRequest(
        "REQ-003", "drop_table", "database", "prod",
        estimated_blast_radius=0, is_reversible=False, risk_level="CRITICAL",
        requested_by="system", description="Remove tabela legada sessions_v1",
    ))
