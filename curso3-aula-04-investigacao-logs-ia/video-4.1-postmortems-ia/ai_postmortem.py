"""
Vídeo 4.1 — Post-mortems assistidos por IA
============================================
Demonstra como usar IA para gerar post-mortems estruturados
automaticamente a partir de dados de incidentes, acelerando
a documentação e a extração de lições aprendidas.

Conceitos demonstrados:
- Reconstrução automática de timeline de incidentes
- Geração de post-mortems no formato SRE (Google)
- Prompt engineering para documentação de incidentes
- Extração automática de action items e lessons learned
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class IncidentEvent:
    """Evento durante um incidente (timeline)."""
    timestamp: datetime
    actor: str  # Sistema ou pessoa
    action: str
    details: str
    event_type: str  # DETECTION, INVESTIGATION, MITIGATION, RESOLUTION, COMMUNICATION


@dataclass
class IncidentData:
    """Dados completos de um incidente para geração do post-mortem."""
    title: str
    severity: str
    started_at: datetime
    detected_at: datetime
    mitigated_at: datetime
    resolved_at: datetime
    affected_services: list[str]
    affected_users_pct: float
    timeline: list[IncidentEvent]
    root_cause: str
    contributing_factors: list[str]
    what_went_well: list[str]
    what_went_wrong: list[str]


def build_incident_scenario() -> IncidentData:
    """Constrói cenário de incidente realista."""
    base = datetime(2024, 8, 15, 9, 0, 0)

    return IncidentData(
        title="Checkout unavailable — payment gateway certificate expired",
        severity="SEV-1",
        started_at=base,
        detected_at=base + timedelta(minutes=8),
        mitigated_at=base + timedelta(minutes=45),
        resolved_at=base + timedelta(hours=1, minutes=20),
        affected_services=["checkout-service", "payment-gateway", "api-gateway"],
        affected_users_pct=35.0,
        timeline=[
            IncidentEvent(base, "payment-gateway", "TLS certificate expired",
                          "Certificate for payments.internal expired at 09:00 UTC", "DETECTION"),
            IncidentEvent(base + timedelta(minutes=2), "checkout-service",
                          "gRPC connections failing", "SSL handshake errors to payment-gateway", "DETECTION"),
            IncidentEvent(base + timedelta(minutes=5), "monitoring",
                          "Error rate alert fired", "checkout error_rate=0.35 (SLO breach)", "DETECTION"),
            IncidentEvent(base + timedelta(minutes=8), "pagerduty",
                          "On-call engineer paged", "Eng. Maria Silva acknowledged", "COMMUNICATION"),
            IncidentEvent(base + timedelta(minutes=12), "maria.silva",
                          "Started investigation", "Checking checkout-service logs", "INVESTIGATION"),
            IncidentEvent(base + timedelta(minutes=18), "maria.silva",
                          "Identified TLS errors", "Found 'certificate has expired' in gRPC logs", "INVESTIGATION"),
            IncidentEvent(base + timedelta(minutes=22), "maria.silva",
                          "Confirmed root cause", "payment-gateway cert expired, not auto-renewed", "INVESTIGATION"),
            IncidentEvent(base + timedelta(minutes=25), "slack",
                          "War room opened", "#incident-2024-0815 created, SRE lead joined", "COMMUNICATION"),
            IncidentEvent(base + timedelta(minutes=35), "carlos.ops",
                          "Emergency cert renewal", "Ran cert-manager force-renew", "MITIGATION"),
            IncidentEvent(base + timedelta(minutes=42), "carlos.ops",
                          "Cert deployed to pods", "Rolling restart of payment-gateway", "MITIGATION"),
            IncidentEvent(base + timedelta(minutes=45), "monitoring",
                          "Error rate recovering", "checkout error_rate=0.02 (recovering)", "MITIGATION"),
            IncidentEvent(base + timedelta(hours=1), "monitoring",
                          "SLO back to healthy", "All SLIs green for 15 minutes", "RESOLUTION"),
            IncidentEvent(base + timedelta(hours=1, minutes=20), "maria.silva",
                          "Incident resolved", "Confirmed stable, closing incident", "RESOLUTION"),
        ],
        root_cause="O certificado TLS do payment-gateway expirou porque o cert-manager "
                   "não conseguiu renovar automaticamente (ACME challenge falhando há 3 dias "
                   "devido a DNS misconfiguration após migração de domínios).",
        contributing_factors=[
            "Alerta de expiração de certificado configurado para 7 dias, mas a renovação falhava há 3",
            "Sem alerta de falha de renovação do cert-manager",
            "DNS do ACME challenge apontando para o cluster antigo após migração",
            "Runbook de renovação manual de certificados desatualizado",
        ],
        what_went_well=[
            "Detecção automática em 5 minutos via SLO breach alert",
            "On-call respondeu em 3 minutos após page",
            "Root cause identificada em 14 minutos",
            "War room criada rapidamente com os engenheiros corretos",
        ],
        what_went_wrong=[
            "Certificado expirou sem aviso prévio efetivo",
            "Tempo de mitigação: 45 min (acima do target de 30 min)",
            "Runbook desatualizado atrasou a renovação manual",
            "35% dos usuários impactados por 45 minutos",
        ],
    )


def generate_postmortem_prompt(incident: IncidentData) -> str:
    """Gera o prompt para a IA criar o post-mortem."""
    timeline_text = "\n".join(
        f"  [{e.timestamp.strftime('%H:%M')}] ({e.event_type}) "
        f"{e.actor}: {e.action} — {e.details}"
        for e in incident.timeline
    )

    return f"""Você é um SRE Lead experiente. Gere um post-mortem completo no formato Google SRE.

DADOS DO INCIDENTE:
==================
Título: {incident.title}
Severidade: {incident.severity}
Início: {incident.started_at.strftime('%Y-%m-%d %H:%M UTC')}
Detecção: {incident.detected_at.strftime('%H:%M UTC')} (TTD: {(incident.detected_at - incident.started_at).seconds // 60} min)
Mitigação: {incident.mitigated_at.strftime('%H:%M UTC')} (TTM: {(incident.mitigated_at - incident.started_at).seconds // 60} min)
Resolução: {incident.resolved_at.strftime('%H:%M UTC')} (TTR: {(incident.resolved_at - incident.started_at).seconds // 60} min)
Serviços afetados: {', '.join(incident.affected_services)}
Usuários impactados: {incident.affected_users_pct}%

TIMELINE:
=========
{timeline_text}

CAUSA RAIZ:
===========
{incident.root_cause}

FATORES CONTRIBUINTES:
=====================
{chr(10).join(f'- {f}' for f in incident.contributing_factors)}

GERE o post-mortem com as seções:
1. Resumo Executivo (3-4 linhas)
2. Impacto (métricas concretas)
3. Timeline detalhada
4. Causa Raiz e Fatores Contribuintes
5. Lessons Learned (o que foi bem / o que falhou)
6. Action Items (com owner e prazo, classificados por prioridade)
7. Métricas de Resposta (TTD, TTM, TTR)

Use formato markdown. Seja objetivo e factual."""


def generate_simulated_postmortem(incident: IncidentData) -> str:
    """Simula a saída que a IA geraria (para demo sem API)."""
    ttd = (incident.detected_at - incident.started_at).seconds // 60
    ttm = (incident.mitigated_at - incident.started_at).seconds // 60
    ttr = (incident.resolved_at - incident.started_at).seconds // 60

    return f"""
# Post-Mortem: {incident.title}

**Severidade:** {incident.severity} | **Data:** {incident.started_at.strftime('%Y-%m-%d')}

## 1. Resumo Executivo

Em {incident.started_at.strftime('%d/%m/%Y')} às {incident.started_at.strftime('%H:%M')} UTC,
o certificado TLS do payment-gateway expirou, causando falha em todas as
transações de checkout. {incident.affected_users_pct}% dos usuários foram
impactados por {ttm} minutos até a mitigação.

## 2. Impacto

| Métrica                  | Valor        |
|--------------------------|--------------|
| Duração do impacto       | {ttm} min    |
| Usuários afetados        | {incident.affected_users_pct}%     |
| Transações perdidas      | ~2.400 (est) |
| Revenue impact estimado  | R$ 18.000    |
| Error budget consumido   | 340%         |

## 3. Causa Raiz

{incident.root_cause}

## 4. Action Items

| Prioridade | Action Item                              | Owner      | Prazo   |
|------------|------------------------------------------|------------|---------|
| P0         | Configurar alerta de falha de renovação  | SRE Team   | 2 dias  |
| P0         | Corrigir DNS do ACME challenge           | Platform   | 1 dia   |
| P1         | Reduzir alerta de expiração para 30 dias | SRE Team   | 1 semana|
| P1         | Atualizar runbook de renovação manual    | On-call    | 1 semana|
| P2         | Adicionar cert-expiry ao dashboard SRE   | Platform   | 2 semanas|
| P2         | Implementar canary check de TLS          | Backend    | Sprint  |

## 5. Métricas de Resposta

| Métrica    | Valor    | Target   | Status |
|------------|----------|----------|--------|
| TTD        | {ttd} min   | < 5 min  | ✅      |
| TTM        | {ttm} min  | < 30 min | ❌      |
| TTR        | {ttr} min  | < 60 min | ❌      |
"""


def run_demo() -> None:
    print("=" * 70)
    print("📝 Demo: Post-Mortems Assistidos por IA")
    print("   Curso 3 — Observabilidade Inteligente")
    print("=" * 70)

    incident = build_incident_scenario()

    # Timeline do incidente
    print(f"\n{'─' * 70}")
    print(f"📋 TIMELINE DO INCIDENTE: {incident.title}")
    print(f"{'─' * 70}")
    for e in incident.timeline:
        type_icons = {
            "DETECTION": "🔍", "INVESTIGATION": "🔬",
            "MITIGATION": "🔧", "RESOLUTION": "✅", "COMMUNICATION": "📢",
        }
        print(f"  {type_icons.get(e.event_type, '  ')} [{e.timestamp.strftime('%H:%M')}] "
              f"{e.actor}: {e.action}")

    # Prompt para IA
    print(f"\n{'─' * 70}")
    print("🤖 PROMPT GERADO PARA A IA")
    print(f"{'─' * 70}")
    prompt = generate_postmortem_prompt(incident)
    # Mostrar apenas as primeiras linhas do prompt
    lines = prompt.split('\n')
    for line in lines[:15]:
        print(f"  {line}")
    print(f"  ... ({len(lines) - 15} linhas adicionais)")

    # Post-mortem gerado
    print(f"\n{'─' * 70}")
    print("📄 POST-MORTEM GERADO (simulação)")
    print(f"{'─' * 70}")
    postmortem = generate_simulated_postmortem(incident)
    print(postmortem)

    # Boas práticas
    print("=" * 70)
    print("📌 BOAS PRÁTICAS DE POST-MORTEMS COM IA")
    print("=" * 70)
    print("""
  1. ALIMENTAR DADOS ESTRUTURADOS: Timeline, métricas, logs resumidos
  2. PEDIR FORMATO ESPECÍFICO: Google SRE, Atlassian, formato interno
  3. REVISAR SEMPRE: IA gera o draft, humanos validam e complementam
  4. INCLUIR CONTEXT: O que funcionou BEM, não apenas o que falhou
  5. ACTION ITEMS COM OWNER: Sem dono e prazo, nada acontece
  6. BLAMELESS: Focar em sistemas e processos, nunca em pessoas

  Na Aula 4.2, veremos como identificar padrões recorrentes
  entre incidentes usando agrupamento estatístico.
    """)


if __name__ == "__main__":
    run_demo()
