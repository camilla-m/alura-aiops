"""
Vídeo 5.4 — Estratégias de adoção de AIOps
===========================================
Demonstra como estruturar um plano gradual e seguro para
adoção de IA na infraestrutura da organização.

Conceitos demonstrados:
- Modelo de maturidade de AIOps (5 níveis)
- Roadmap progressivo de adoção
- Identificação de quick wins e casos de alto valor
- Gestão de mudança e resistência organizacional
- Métricas de sucesso para cada nível de maturidade
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MaturityLevel:
    """Nível de maturidade de AIOps."""
    level: int
    name: str
    description: str
    capabilities: list[str]
    key_metrics: list[str]
    typical_duration_months: int
    prerequisites: list[str]
    common_pitfalls: list[str]


@dataclass
class AdoptionRoadmapItem:
    """Item do roadmap de adoção."""
    phase: int
    name: str
    duration_weeks: int
    effort: str       # LOW | MEDIUM | HIGH
    impact: str       # LOW | MEDIUM | HIGH
    actions: list[str]
    success_criteria: list[str]
    team_involved: list[str]


MATURITY_MODEL: list[MaturityLevel] = [
    MaturityLevel(
        level=1, name="Observabilidade Básica",
        description="Coleta centralizada de logs, métricas e traces com alertas manuais.",
        capabilities=["Centralized logging", "Metrics collection", "Basic alerting", "Dashboards"],
        key_metrics=["MTTR", "Alert volume", "Coverage (% de serviços instrumentados)"],
        typical_duration_months=3,
        prerequisites=["Infraestrutura de observabilidade definida", "Processo de on-call estabelecido"],
        common_pitfalls=["Excesso de logs sem estrutura", "Alertas genéricos sem contexto"],
    ),
    MaturityLevel(
        level=2, name="Detecção Inteligente",
        description="Thresholds dinâmicos, detecção de anomalias e redução de alert fatigue.",
        capabilities=["Dynamic baselines", "Anomaly detection", "Alert correlation", "Noise reduction"],
        key_metrics=["False positive rate", "Alert-to-action ratio", "MTTA"],
        typical_duration_months=3,
        prerequisites=["Nível 1 consolidado", "Histórico de 4+ semanas de métricas"],
        common_pitfalls=["Confiança excessiva na IA sem validação", "Baselines sem sazonalidade semanal"],
    ),
    MaturityLevel(
        level=3, name="Diagnóstico Assistido",
        description="IA integrada no troubleshooting, correlação change-incident, análise de logs.",
        capabilities=["AI-assisted RCA", "Change correlation", "Log analysis with LLM", "Context-aware triage"],
        key_metrics=["Time-to-diagnose", "RCA accuracy", "MTTR reduction"],
        typical_duration_months=4,
        prerequisites=["Nível 2 consolidado", "Acesso a LLM API", "Change management integrado"],
        common_pitfalls=["Prompt engineering mal calibrado", "Contexto insuficiente para o LLM"],
    ),
    MaturityLevel(
        level=4, name="Remediação Automatizada",
        description="Self-healing com guardrails, runbooks automatizados e aprovação seletiva.",
        capabilities=["Self-healing runbooks", "Guardrails", "Human-in-the-loop", "Automated rollbacks"],
        key_metrics=["Auto-remediation rate", "Incidents requiring human action", "MTTR P1"],
        typical_duration_months=6,
        prerequisites=["Nível 3 consolidado", "Runbooks documentados", "Aprovação organizacional"],
        common_pitfalls=["Automações sem circuit breaker", "Blast radius não calculado"],
    ),
    MaturityLevel(
        level=5, name="Operações Preditivas",
        description="Previsão de falhas, capacity planning automático e otimização contínua.",
        capabilities=["Failure prediction", "Capacity forecast", "Cost optimization", "Continuous improvement"],
        key_metrics=["Incidents prevented", "Capacity utilization", "Cloud cost efficiency"],
        typical_duration_months=12,
        prerequisites=["Nível 4 consolidado", "Cultura de dados estabelecida", "ML team envolvido"],
        common_pitfalls=["Modelos treinados com dados insuficientes", "Drift de modelo não monitorado"],
    ),
]


ADOPTION_ROADMAP: list[AdoptionRoadmapItem] = [
    AdoptionRoadmapItem(
        phase=1, name="Diagnóstico e Quick Wins",
        duration_weeks=4, effort="LOW", impact="MEDIUM",
        actions=[
            "Auditar alertas existentes — identificar os 10 mais ruidosos",
            "Calcular Signal-to-Noise Ratio atual do sistema de alertas",
            "Mapear o top 5 de incidentes recorrentes (candidatos a runbook)",
            "Identificar gaps de observabilidade (serviços sem instrumentação)",
        ],
        success_criteria=[
            "Mapa de maturidade atual documentado",
            "Quick wins identificados com ROI estimado",
            "Buy-in da liderança obtido com dados",
        ],
        team_involved=["SRE Lead", "Engineering Manager"],
    ),
    AdoptionRoadmapItem(
        phase=2, name="Observabilidade Unificada",
        duration_weeks=6, effort="MEDIUM", impact="HIGH",
        actions=[
            "Implementar logging estruturado em todos os serviços tier-1",
            "Configurar correlação de trace_id entre logs, métricas e traces",
            "Migrar alertas estáticos para baselines dinâmicos (começar por 3 serviços)",
            "Criar dashboard de signal health (SNR, false positive rate)",
        ],
        success_criteria=[
            "100% dos serviços tier-1 com trace_id propagado",
            "False positive rate reduzido em 40%",
            "Alert-to-action ratio > 60%",
        ],
        team_involved=["SRE Team", "Platform Engineers"],
    ),
    AdoptionRoadmapItem(
        phase=3, name="IA no Troubleshooting",
        duration_weeks=8, effort="HIGH", impact="HIGH",
        actions=[
            "Integrar LLM no processo de triagem (prompt library estabelecida)",
            "Implementar change-incident correlation automática",
            "Criar biblioteca de prompts validados para cenários comuns",
            "Treinar o time em prompt engineering para operações",
        ],
        success_criteria=[
            "Time-to-diagnose reduzido em 50%",
            "LLM usado em >70% dos incidentes P1/P2",
            "Prompt library com 20+ templates validados",
        ],
        team_involved=["SRE Team", "SRE Lead", "Gerência TI"],
    ),
    AdoptionRoadmapItem(
        phase=4, name="Automação Controlada",
        duration_weeks=10, effort="HIGH", impact="HIGH",
        actions=[
            "Codificar os top 5 runbooks como código executável",
            "Implementar motor de guardrails com blast radius estimation",
            "Configurar human-in-the-loop para ações de risco MEDIUM+",
            "Monitorar auto-remediation rate e ajustar regras",
        ],
        success_criteria=[
            "Auto-remediation rate > 30% dos incidentes",
            "Zero incidentes agravados por automação",
            "MTTR P1 reduzido em 40%",
        ],
        team_involved=["SRE Team", "Security Team", "Engineering Manager"],
    ),
]


def print_maturity_model() -> None:
    print("\n" + "=" * 70)
    print("📊 MODELO DE MATURIDADE AIOPS — 5 NÍVEIS")
    print("=" * 70)

    for level in MATURITY_MODEL:
        print(f"\n  {'─'*60}")
        print(f"  NÍVEL {level.level}: {level.name}")
        print(f"  {'─'*60}")
        print(f"  {level.description}")
        print(f"\n  Capacidades: {', '.join(level.capabilities)}")
        print(f"  Duração estimada: {level.typical_duration_months} meses")
        print(f"\n  ⚠️  Armadilhas comuns:")
        for p in level.common_pitfalls:
            print(f"     - {p}")


def print_adoption_roadmap() -> None:
    print("\n" + "=" * 70)
    print("🗺️  ROADMAP DE ADOÇÃO — FASES PROGRESSIVAS")
    print("=" * 70)

    for item in ADOPTION_ROADMAP:
        effort_icon  = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(item.effort, "⚪")
        impact_icon  = {"LOW": "📉", "MEDIUM": "📊", "HIGH": "📈"}.get(item.impact, "—")
        print(f"\n  FASE {item.phase}: {item.name}")
        print(f"  Duração: {item.duration_weeks} semanas | Esforço: {effort_icon} {item.effort} | Impacto: {impact_icon} {item.impact}")
        print(f"\n  Ações:")
        for action in item.actions:
            print(f"    • {action}")
        print(f"\n  Critérios de sucesso:")
        for sc in item.success_criteria:
            print(f"    ✓ {sc}")


def print_resistance_guide() -> None:
    print("\n" + "=" * 70)
    print("🧠 GESTÃO DE RESISTÊNCIA — COMO INTRODUZIR AIOPS SEM TRAUMA")
    print("=" * 70)
    print("""
  OBJEÇÕES COMUNS E COMO RESPONDER:

  ❓ "A IA vai errar e piorar o incidente"
  ✅ Comece com IA apenas em modo sugestão (sem ação automática).
     Apresente dados de acurácia antes de ativar self-healing.
     Guardrails garantem que ações destrutivas sempre passem por humanos.

  ❓ "Vamos perder o controle das operações"
  ✅ AIOps aumenta visibilidade, não reduz controle.
     Human-in-the-loop é um princípio fundamental, não opcional.
     O time aprova, a IA executa — sempre com audit trail completo.

  ❓ "Vai ser muito complexo de manter"
  ✅ Comece simples: 3 runbooks, 5 monitores dinâmicos.
     Complexidade aumenta com maturidade e experiência do time.
     Plataformas como Datadog/Dynatrace já têm 80% da IA embutida.

  ❓ "Não temos dados suficientes para treinar modelos"
  ✅ Baselines dinâmicos precisam de apenas 2-4 semanas de histórico.
     Comece com ML pré-treinado das plataformas SaaS.
     Modelos customizados são fase 5 — não é preciso no início.

  📌 ESTRATÉGIA: Prove valor cedo, escale com confiança.
     Primeiro incidente resolvido automaticamente gera mais buy-in
     do que qualquer apresentação de slides.
    """)


if __name__ == "__main__":
    print("🔬 Demo: Estratégias de Adoção de AIOps")
    print("     Nível 1 — AIOps & Automação de Incidentes")

    print_maturity_model()
    print_adoption_roadmap()
    print_resistance_guide()
