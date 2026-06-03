"""
Vídeo 3.3 — Relacionando mudanças e incidentes
===============================================
Demonstra como cruzar cronogramas de deploys e alterações
de configuração com o surgimento de incidentes para
identificar change-induced failures (drift).

Conceitos demonstrados:
- Change-incident correlation (temporal proximity)
- Análise de correlação por serviço e janela de tempo
- Detecção de "deployment drift" via comparação de versões
- Geração automatizada de relatórios de change-impact
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class ChangeEvent:
    """Representa uma mudança no sistema (deploy, config change, etc.)."""
    change_id: str
    change_type: str    # DEPLOY | CONFIG | INFRASTRUCTURE | DATABASE
    service: str
    version: Optional[str]
    author: str
    timestamp: datetime
    description: str
    rollback_available: bool = True


@dataclass
class Incident:
    """Representa um incidente operacional."""
    incident_id: str
    title: str
    affected_services: list[str]
    started_at: datetime
    severity: str


@dataclass
class ChangeCorrelation:
    """Resultado da correlação entre uma mudança e um incidente."""
    change: ChangeEvent
    incident: Incident
    time_delta_minutes: float
    service_overlap: bool
    correlation_score: float  # 0-1
    verdict: str              # LIKELY_CAUSE | POSSIBLE_CAUSE | UNLIKELY


# ---------------------------------------------------------------------------
# Motor de correlação change-incident
# ---------------------------------------------------------------------------

def correlate_changes_with_incident(
    changes: list[ChangeEvent],
    incident: Incident,
    pre_incident_window_hours: int = 4,
    post_incident_window_hours: int = 1,
) -> list[ChangeCorrelation]:
    """
    Correlaciona mudanças com um incidente usando janelas de tempo e
    sobreposição de serviços afetados.

    Lógica:
    - Mudanças dentro da janela pré-incidente são candidatas
    - Mudanças nos mesmos serviços afetados têm score mais alto
    - Mais recente = maior correlação (decay temporal)
    """
    window_start = incident.started_at - timedelta(hours=pre_incident_window_hours)
    window_end   = incident.started_at + timedelta(hours=post_incident_window_hours)

    correlations = []

    for change in changes:
        if not (window_start <= change.timestamp <= window_end):
            continue

        delta_minutes = (incident.started_at - change.timestamp).total_seconds() / 60

        # Sobreposição de serviços
        service_overlap = (
            change.service in incident.affected_services or
            any(svc in incident.affected_services for svc in [change.service])
        )

        # Score de correlação
        # Decai com o tempo (mudanças mais antigas têm score menor)
        max_minutes = pre_incident_window_hours * 60
        time_score = max(0, 1 - delta_minutes / max_minutes) if delta_minutes >= 0 else 0.5
        overlap_score = 0.5 if service_overlap else 0.1
        type_score = 0.3 if change.change_type == "DEPLOY" else 0.2

        correlation_score = round(time_score * 0.5 + overlap_score * 0.4 + type_score * 0.1, 3)

        # Veredicto
        if correlation_score >= 0.65 and service_overlap:
            verdict = "🔴 CAUSA PROVÁVEL"
        elif correlation_score >= 0.35:
            verdict = "🟡 CAUSA POSSÍVEL"
        else:
            verdict = "⚪ IMPROVÁVEL"

        correlations.append(ChangeCorrelation(
            change=change, incident=incident,
            time_delta_minutes=round(delta_minutes, 1),
            service_overlap=service_overlap,
            correlation_score=correlation_score,
            verdict=verdict,
        ))

    return sorted(correlations, key=lambda c: c.correlation_score, reverse=True)


def print_correlation_report(
    correlations: list[ChangeCorrelation],
    incident: Incident,
) -> None:
    print("\n" + "=" * 70)
    print(f"🔍 CORRELAÇÃO MUDANÇAS × INCIDENTE")
    print("=" * 70)
    print(f"\n  Incidente : {incident.incident_id} — {incident.title}")
    print(f"  Início    : {incident.started_at.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Afetados  : {', '.join(incident.affected_services)}")
    print(f"\n  Mudanças analisadas na janela: {len(correlations)}\n")

    if not correlations:
        print("  ⚠️  Nenhuma mudança encontrada na janela de tempo configurada.")
        return

    for c in correlations:
        delta_str = f"+{c.time_delta_minutes:.0f} min" if c.time_delta_minutes >= 0 else f"{c.time_delta_minutes:.0f} min (após início)"
        print(f"  {'─'*60}")
        print(f"  {c.verdict}")
        print(f"  [{c.change.change_id}] {c.change.change_type}: {c.change.service} {c.change.version or ''}")
        print(f"  Autor       : {c.change.author}")
        print(f"  Descrição   : {c.change.description}")
        print(f"  Tempo antes : {delta_str}")
        print(f"  Serviço ↔  incidente: {'✅ sim' if c.service_overlap else '❌ não'}")
        print(f"  Score       : {c.correlation_score:.0%}")
        print(f"  Rollback    : {'✅ disponível' if c.change.rollback_available else '❌ não disponível'}")
        print()


# ---------------------------------------------------------------------------
# Dados do cenário
# ---------------------------------------------------------------------------

def build_scenario() -> tuple[list[ChangeEvent], Incident]:
    incident_start = datetime(2024, 6, 3, 9, 2, 0)

    changes = [
        ChangeEvent("CHG-001", "DEPLOY", "auth-service", "v2.3.1",
                    "alice@company.com", incident_start - timedelta(minutes=17),
                    "Migração para novo driver de PostgreSQL (pg v5.0)", True),
        ChangeEvent("CHG-002", "DATABASE", "database", None,
                    "bob@company.com", incident_start - timedelta(minutes=32),
                    "Schema migration: adição de índice em sessions.user_id", False),
        ChangeEvent("CHG-003", "CONFIG", "api-gateway", None,
                    "carol@company.com", incident_start - timedelta(hours=2),
                    "Ajuste de timeout upstream de 60s para 30s", True),
        ChangeEvent("CHG-004", "DEPLOY", "frontend", "v1.8.0",
                    "dave@company.com", incident_start - timedelta(hours=6),
                    "Update de dependências do frontend (sem mudanças funcionais)", True),
        ChangeEvent("CHG-005", "INFRASTRUCTURE", "database", None,
                    "ops-team@company.com", incident_start - timedelta(days=1),
                    "Upgrade de PostgreSQL 14 → 15 (janela de manutenção)", True),
    ]

    incident = Incident(
        incident_id="INC-2024-0603-001",
        title="Frontend retornando 503 — auth-service degradado",
        affected_services=["auth-service", "api-gateway", "frontend", "database"],
        started_at=incident_start,
        severity="P1",
    )

    return changes, incident


if __name__ == "__main__":
    print("🔬 Demo: Relacionando Mudanças e Incidentes")
    print("     Nível 1 — AIOps & Automação de Incidentes")

    changes, incident = build_scenario()
    correlations = correlate_changes_with_incident(changes, incident)
    print_correlation_report(correlations, incident)

    print("=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print(f"""
  Com base na análise, a mudança mais provável de ter causado
  o incidente é o CHG-001 (deploy auth-service v2.3.1), pois:
  - Ocorreu 17 minutos antes do incidente
  - Afeta diretamente o serviço degradado
  - Envolveu mudança de driver de banco de dados
  - Score de correlação mais alto ({correlations[0].correlation_score:.0%})

  Ação imediata: avaliar rollback para auth-service v2.3.0
  e investigar compatibilidade do novo driver com o pool size.
    """)
