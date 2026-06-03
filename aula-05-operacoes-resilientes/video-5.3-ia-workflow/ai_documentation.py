"""
Vídeo 5.3 — IA no workflow do time de operações
================================================
Demonstra práticas colaborativas com IA para geração de
post-mortems e runbooks corporativos padronizados.

Conceitos demonstrados:
- Geração automática de post-mortem com IA
- Templates corporativos de runbooks com assistência de LLM
- Padronização e revisão colaborativa assistida
- Repositório de conhecimento operacional (knowledge base)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class IncidentData:
    """Dados estruturados de um incidente para gerar documentação."""
    incident_id: str
    title: str
    severity: str
    started_at: datetime
    resolved_at: datetime
    root_cause: str
    affected_services: list[str]
    users_impacted: int
    revenue_impact: float
    actions_taken: list[str]
    contributing_factors: list[str]
    team_members: list[str]


def generate_postmortem_with_ai_prompt(incident: IncidentData) -> str:
    """
    Gera o prompt para criar um post-mortem completo usando LLM.
    Demonstra como estruturar o input para obter documentação de alta qualidade.
    """
    duration_min = int((incident.resolved_at - incident.started_at).total_seconds() / 60)
    actions_text = "\n".join(f"- {a}" for a in incident.actions_taken)
    factors_text  = "\n".join(f"- {f}" for f in incident.contributing_factors)

    return f"""Você é um SRE sênior especialista em documentação técnica e gestão de incidentes.

Gere um post-mortem completo e profissional para o seguinte incidente:

DADOS DO INCIDENTE:
===================
ID             : {incident.incident_id}
Título         : {incident.title}
Severidade     : {incident.severity}
Duração        : {duration_min} minutos
Serviços       : {', '.join(incident.affected_services)}
Usuários       : {incident.users_impacted:,}
Impacto $      : R$ {incident.revenue_impact:,.0f}

Causa Raiz     : {incident.root_cause}

Fatores Contribuintes:
{factors_text}

Ações de Remediação:
{actions_text}

Time Envolvido: {', '.join(incident.team_members)}

FORMATO REQUERIDO:
==================
Gere o post-mortem seguindo exatamente esta estrutura:

1. **Sumário Executivo** (máx. 3 parágrafos, linguagem não-técnica)
2. **Impacto** (quantitativo e qualitativo)
3. **Timeline** (cronológico, com timestamps relativos ao início do incidente)
4. **Causa Raiz** (técnica, com diagrama de causalidade em texto)
5. **Fatores Contribuintes** (o que facilitou a ocorrência)
6. **Ações de Remediação** (o que foi feito durante o incidente)
7. **Action Items Preventivos** (tabela: ação | responsável | prazo | prioridade)
8. **Lições Aprendidas** (3-5 insights para o time)
9. **Métricas do Incidente** (MTTR, MTTA, SLO burn, usuários impactados)

Tom: técnico mas acessível. Use dados concretos. Evite jargões sem explicação.
"""


def generate_runbook_with_ai_prompt(
    runbook_name: str,
    trigger_condition: str,
    service: str,
    symptoms: list[str],
    known_causes: list[str],
) -> str:
    """Gera o prompt para criar um runbook padronizado com LLM."""
    symptoms_text = "\n".join(f"- {s}" for s in symptoms)
    causes_text   = "\n".join(f"- {c}" for c in known_causes)

    return f"""Você é um SRE sênior com expertise em automação operacional.

Crie um runbook operacional padronizado para o seguinte cenário:

CONTEXTO:
=========
Runbook      : {runbook_name}
Trigger      : {trigger_condition}
Serviço      : {service}

Sintomas Observados:
{symptoms_text}

Causas Conhecidas:
{causes_text}

FORMATO REQUERIDO:
==================
Crie o runbook seguindo exatamente esta estrutura em Markdown:

# {runbook_name}

## Contexto
(Explique quando este runbook deve ser usado)

## Pré-requisitos
(Acesso, ferramentas, permissões necessárias)

## Diagnóstico Rápido (< 5 min)
(Comandos para validar cada causa conhecida)

## Procedimentos de Remediação
(Subseções por causa: ### Causa 1, ### Causa 2, etc.)
(Para cada causa: passos numerados, comandos exatos, output esperado)

## Validação
(Como confirmar que o problema foi resolvido)

## Escalação
(Quando e para quem escalar se os procedimentos não funcionarem)

## Histórico de Mudanças
| Data | Autor | Alteração |
|------|-------|-----------|

REQUISITOS:
- Use comandos kubectl, psql, redis-cli específicos e executáveis
- Inclua output esperado de cada comando para guiar o operador
- Destaque riscos com [⚠️ ATENÇÃO: ...] para ações destrutivas
- Indique o tempo estimado de cada procedimento
"""


def print_ai_workflow_guide() -> None:
    """Guia de práticas para uso de IA no workflow operacional."""
    print("\n" + "=" * 65)
    print("🤖 IA NO WORKFLOW DO TIME DE OPERAÇÕES")
    print("=" * 65)

    use_cases = [
        ("Post-Mortem", "Gera rascunho estruturado em segundos. O time valida e enriquece.",
         "50-70% de redução no tempo de escrita"),
        ("Runbooks", "Sugere procedimentos baseados em causas conhecidas e melhores práticas.",
         "60% mais rápido que escrita manual"),
        ("War Room Updates", "Gera status updates padronizados a cada 15 min automaticamente.",
         "Comunicação mais consistente"),
        ("Knowledge Base", "Transforma incidentes em artigos de KB estruturados.",
         "Base de conhecimento sempre atualizada"),
        ("Revisão de Alertas", "Analisa o catálogo de alertas e sugere consolidações.",
         "30-50% de redução de noise"),
    ]

    for use_case, description, benefit in use_cases:
        print(f"\n  📌 {use_case}")
        print(f"     {description}")
        print(f"     → Benefício: {benefit}")

    print(f"""
  ─────────────────────────────────────────────

  BOAS PRÁTICAS:
  ✅ Use IA para acelerar, não para substituir a revisão humana
  ✅ Sempre valide com dados reais antes de publicar documentação gerada
  ✅ Crie templates customizados para o contexto da sua empresa
  ✅ Mantenha histórico de prompts que funcionaram bem (prompt library)
  ❌ Não publique post-mortems sem revisão do time
  ❌ Não use IA para decisões de remediação em produção sem guardrails
    """)


if __name__ == "__main__":
    print("🔬 Demo: IA no Workflow do Time de Operações")
    print("     Nível 1 — AIOps & Automação de Incidentes")

    incident = IncidentData(
        incident_id="INC-2024-0603-001",
        title="Frontend 503 — auth-service connection pool esgotado",
        severity="P1",
        started_at=datetime(2024, 6, 3, 9, 2, 0),
        resolved_at=datetime(2024, 6, 3, 9, 20, 0),
        root_cause="Deploy auth-service v2.3.1 introduziu driver PostgreSQL incompatível com max_connections=100",
        affected_services=["auth-service", "api-gateway", "frontend", "payment-service"],
        users_impacted=50_000,
        revenue_impact=90_000.0,
        actions_taken=[
            "Identificado deploy CHG-001 como causa raiz (T+5min)",
            "Queries travadas terminadas via pg_terminate_backend (T+8min)",
            "max_connections aumentado para 200 (T+10min)",
            "Rolling restart auth-service (T+12min)",
            "Normalização confirmada: error_rate < 1% (T+18min)",
        ],
        contributing_factors=[
            "Falta de teste de carga no pipeline de CI/CD do auth-service",
            "max_connections configurado sem margem de segurança",
            "Ausência de PgBouncer para connection pooling externo",
            "Alerta de connection pool com threshold estático (não-preditivo)",
        ],
        team_members=["Alice (SRE)", "Bob (DBA)", "Carol (Lead)"],
    )

    print_ai_workflow_guide()

    print("\n" + "=" * 65)
    print("PROMPT GERADO — Post-Mortem com IA:")
    print("=" * 65)
    print(generate_postmortem_with_ai_prompt(incident))

    print("\n" + "=" * 65)
    print("PROMPT GERADO — Runbook com IA:")
    print("=" * 65)
    print(generate_runbook_with_ai_prompt(
        "auth-service-connection-pool-recovery",
        "connection_pool_active > 90% OR auth-service error_rate > 50%",
        "auth-service / PostgreSQL",
        symptoms=["auth-service retornando 503", "PostgreSQL connections > 90/100", "Latência p99 > 5s"],
        known_causes=["Queries travadas bloqueando conexões", "max_connections configurado muito baixo", "Driver de conexão com bug de leak"],
    ))
