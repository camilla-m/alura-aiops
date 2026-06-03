"""
Vídeo 4.3 — IA integrada ao fluxo de incidentes
=================================================
Demonstra como configurar o envio automático de resumos de
incidentes e sugestões de ações para salas de crise,
otimizando a comunicação síncrona do time de resposta.

Conceitos demonstrados:
- Geração automática de War Room summaries com IA
- Templates de mensagens para diferentes canais (Slack, PagerDuty)
- Status updates automáticos durante o incidente
- Post-mortem draft automatizado
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class IncidentTimeline:
    """Timeline estruturada de um incidente."""
    events: list[tuple[datetime, str]] = field(default_factory=list)

    def add(self, ts: datetime, event: str) -> None:
        self.events.append((ts, event))

    def format(self) -> str:
        return "\n".join(
            f"  {ts.strftime('%H:%M UTC')} — {event}"
            for ts, event in sorted(self.events)
        )


@dataclass
class IncidentReport:
    """Relatório completo de um incidente para comunicação."""
    incident_id: str
    title: str
    severity: str
    started_at: datetime
    resolved_at: Optional[datetime]
    affected_services: list[str]
    root_cause: str
    impact: str
    timeline: IncidentTimeline
    actions_taken: list[str]
    current_status: str  # INVESTIGATING | IDENTIFIED | MITIGATING | RESOLVED


def generate_war_room_summary(report: IncidentReport) -> str:
    """
    Gera o resumo inicial para a war room (Slack/Teams).
    Formato conciso para leitura rápida durante o incidente.
    """
    severity_emoji = {"P1": "🔴", "P2": "🟡", "P3": "🟢"}.get(report.severity, "⚪")
    status_emoji = {
        "INVESTIGATING": "🔍", "IDENTIFIED": "🎯",
        "MITIGATING": "🔧", "RESOLVED": "✅"
    }.get(report.current_status, "❓")

    duration = ""
    if report.resolved_at:
        delta = report.resolved_at - report.started_at
        duration = f"Duração: {int(delta.total_seconds() // 60)} min\n"

    return f"""{severity_emoji} *INCIDENTE {report.severity} — {report.incident_id}*
Status: {status_emoji} {report.current_status}
{duration}
*Resumo:* {report.title}
*Serviços:* {', '.join(report.affected_services)}
*Início:* {report.started_at.strftime('%H:%M UTC')}

*Impacto:* {report.impact}

*Causa Raiz:* {report.root_cause if report.root_cause else '_Investigando..._'}

*Últimas ações:*
{chr(10).join('• ' + a for a in report.actions_taken[-3:])}

_Atualizações a cada 15 min ou quando houver mudança de status._
"""


def generate_status_update(
    report: IncidentReport,
    update_number: int,
    new_findings: str,
    next_steps: list[str],
) -> str:
    """Gera uma atualização de status durante o incidente."""
    return f"""📢 *UPDATE #{update_number} — {report.incident_id}*
{datetime.now().strftime('%H:%M UTC')}

*Status atual:* {report.current_status}

*Novidades:*
{new_findings}

*Próximos passos:*
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(next_steps))}

_Próximo update em 15 min._
"""


def generate_postmortem_draft(report: IncidentReport) -> str:
    """
    Gera o rascunho de post-mortem automaticamente.
    Em produção, este texto seria enviado a um LLM para enriquecimento.
    """
    duration_min = 0
    if report.resolved_at:
        duration_min = int((report.resolved_at - report.started_at).total_seconds() // 60)

    return f"""# Post-Mortem: {report.incident_id}
## {report.title}

**Data:** {report.started_at.strftime('%Y-%m-%d')}
**Severidade:** {report.severity}
**Duração:** {duration_min} minutos
**Status:** {report.current_status}

---

## Resumo Executivo

<!-- TODO: expandir com LLM -->
Incidente de severidade {report.severity} afetando {', '.join(report.affected_services)}.
Durou {duration_min} minutos desde a detecção até a resolução.
Causa raiz: {report.root_cause}

---

## Impacto

{report.impact}

---

## Timeline

{report.timeline.format()}

---

## Causa Raiz

{report.root_cause}

---

## Ações de Remediação Tomadas

{chr(10).join(f'- {a}' for a in report.actions_taken)}

---

## Ações Preventivas (Action Items)

| Ação | Responsável | Prazo | Status |
|------|-------------|-------|--------|
| Configurar PgBouncer para connection pooling | DBA Team | 2 semanas | Pendente |
| Adicionar teste de carga no pipeline do auth-service | SRE Team | 1 semana | Pendente |
| Aumentar max_connections de forma permanente | DBA Team | 3 dias | Pendente |
| Criar alerta de baseline em connections_active | SRE Team | 1 semana | Pendente |

---

## Lições Aprendidas

<!-- TODO: preencher em revisão com o time -->
1. 
2. 
3. 

---

*Documento gerado automaticamente. Revisar e enriquecer com o time.*
"""


def build_incident_demo() -> IncidentReport:
    """Constrói o incidente demo para os exemplos."""
    t0 = datetime(2024, 6, 3, 9, 2, 0)
    timeline = IncidentTimeline()
    timeline.add(t0,                    "Primeiros alertas: auth-service error_rate > 80%")
    timeline.add(t0 + timedelta(min=2), "War room criada, time acionado")
    timeline.add(t0 + timedelta(min=5), "Causa raiz identificada: connection pool esgotado")
    timeline.add(t0 + timedelta(min=8), "Runbook de recuperação iniciado")
    timeline.add(t0 + timedelta(min=12),"Rolling restart do auth-service concluído")
    timeline.add(t0 + timedelta(min=15),"Serviços normalizados, error_rate < 1%")
    timeline.add(t0 + timedelta(min=18),"Incidente resolvido")

    return IncidentReport(
        incident_id="INC-2024-0603-001",
        title="Frontend 503 — Connection pool esgotado no auth-service",
        severity="P1",
        started_at=t0,
        resolved_at=t0 + timedelta(minutes=18),
        affected_services=["auth-service", "api-gateway", "frontend", "payment-service"],
        root_cause="Deploy auth-service v2.3.1 introduziu novo driver PostgreSQL que não respeita o max_connections configurado (100), esgotando o pool em condições de carga normal.",
        impact="42% dos usuários não conseguiram acessar o frontend. 100% das transações de pagamento bloqueadas por 18 minutos. Estimativa: ~R$ 90.000 de receita impactada.",
        timeline=timeline,
        actions_taken=[
            "Identificado deploy CHG-001 como causa provável (17 min antes do incidente)",
            "Terminadas queries travadas no PostgreSQL (pg_terminate_backend)",
            "max_connections aumentado temporariamente para 200",
            "Rolling restart do auth-service (3 pods)",
            "Erro rate normalizado para <1% em 15 minutos",
        ],
        current_status="RESOLVED",
    )


if __name__ == "__main__":
    print("🔬 Demo: IA Integrada ao Fluxo de Incidentes")
    print("     Nível 1 — AIOps & Automação de Incidentes")

    report = build_incident_demo()

    print("\n" + "=" * 65)
    print("1. MENSAGEM DE WAR ROOM (Slack/Teams):")
    print("=" * 65)
    print(generate_war_room_summary(report))

    print("\n" + "=" * 65)
    print("2. STATUS UPDATE #2:")
    print("=" * 65)
    print(generate_status_update(
        report, update_number=2,
        new_findings="Causa raiz confirmada: deploy auth-service v2.3.1 com novo driver PostgreSQL. Rolling restart em andamento.",
        next_steps=["Aguardar conclusão do rolling restart (ETA: 3 min)", "Validar error rate pós-restart", "Confirmar normalização com equipe de produto"],
    ))

    print("\n" + "=" * 65)
    print("3. RASCUNHO DE POST-MORTEM:")
    print("=" * 65)
    print(generate_postmortem_draft(report))
