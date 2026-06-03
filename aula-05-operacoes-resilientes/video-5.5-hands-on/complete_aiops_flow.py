"""
Vídeo 5.5 — Hands-on: Fluxo operacional completo com AIOps
============================================================
EXERCÍCIO INTEGRADOR — Aula 5 (conclusão do curso)

Orquestra um cenário fim a fim consolidando TODAS as habilidades:
  1. Observabilidade inteligente (correlação de sinais)
  2. Detecção de anomalias com baseline dinâmico
  3. Investigação assistida por IA
  4. Automação com guardrails e aprovação humana
  5. Documentação automática e pipeline integrado

Este é o exercício conclusivo do curso.

Execute:
  python complete_aiops_flow.py
"""

from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path

# Importa módulos de todas as aulas
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from aula_01_volume_de_sinais.video_1_1_alert_storm.alert_storm_demo import simulate_alert_storm, analyze_alert_storm
from aula_01_volume_de_sinais.video_1_2_correlacao_incidentes.event_correlator import EventCorrelator, Signal, SignalType
from aula_01_volume_de_sinais.video_1_3_priorizacao.impact_scorer import calculate_impact_score

from aula_02_deteccao_de_anomalias.video_2_1_anomalias_infra.anomaly_detector import generate_cpu_series, detect_by_zscore
from aula_02_deteccao_de_anomalias.video_2_2_baselines_dinamicos.dynamic_baseline import DynamicBaseline, generate_weekly_metric

from aula_03_investigacao_assistida_ia.video_3_2_analise_logs.log_analyzer_ai import SAMPLE_LOGS, extract_patterns_local
from aula_03_investigacao_assistida_ia.video_3_3_mudancas_incidentes.change_correlator import build_scenario, correlate_changes_with_incident
from aula_03_investigacao_assistida_ia.video_3_4_contexto_distribuido.topology_context import TOPOLOGY, topology_to_prompt_context

from aula_04_automacao_e_resposta.video_4_2_runbooks.runbook_executor import create_auth_service_recovery_runbook
from aula_04_automacao_e_resposta.video_4_4_guardrails.guardrail_engine import GuardrailEngine, AutomationRequest

from aula_05_operacoes_resilientes.video_5_2_fluxos_integrados.unified_pipeline import UnifiedOperationsPipeline
from aula_05_operacoes_resilientes.video_5_3_ia_workflow.ai_documentation import IncidentData, generate_postmortem_with_ai_prompt


def section(title: str) -> None:
    print(f"\n{'='*65}")
    print(f"  {title}")
    print(f"{'='*65}")


def run_complete_flow() -> None:
    print("=" * 65)
    print("🚀 EXERCÍCIO INTEGRADOR — FLUXO AIOPS COMPLETO")
    print("   Curso 2: AIOps & Automação de Incidentes")
    print("   Instrutora: Camilla Martins | Alura")
    print("=" * 65)
    print("""
  Você vai executar o fluxo completo de um incidente real:
  
  [AULA 1] Observabilidade → correlação de sinais
  [AULA 2] Anomalia detectada com baseline dinâmico
  [AULA 3] Investigação assistida por IA
  [AULA 4] Remediação automatizada com guardrails
  [AULA 5] Pipeline integrado + documentação automática
  """)
    input("  ▶ Pressione ENTER para iniciar o exercício...")

    t_start = datetime.now()

    # ──────────────────────────────────────────────────────────────────
    # BLOCO 1 — AULA 1: Observabilidade e correlação
    # ──────────────────────────────────────────────────────────────────
    section("BLOCO 1/5 — AULA 1: Observabilidade e correlação de sinais")

    # Alert storm
    alerts = simulate_alert_storm("database")
    analyze_alert_storm(alerts)
    time.sleep(0.5)

    # Triagem por impact score
    triage = calculate_impact_score("database")
    print(f"\n  🎯 Impact Score: {triage.impact_score}/100 → {triage.priority}")
    print(f"     {triage.recommended_action}")

    # ──────────────────────────────────────────────────────────────────
    # BLOCO 2 — AULA 2: Detecção de anomalias
    # ──────────────────────────────────────────────────────────────────
    section("BLOCO 2/5 — AULA 2: Detecção de anomalias com baseline dinâmico")

    cpu_series = generate_cpu_series(hours=24, inject_anomaly_at=9)
    zscore_results = detect_by_zscore(cpu_series, z_threshold=2.5)
    anomalies = [r for r in zscore_results if r.is_anomaly]
    print(f"\n  CPU série (24h): {len(cpu_series)} pontos analisados")
    print(f"  Anomalias detectadas (Z-Score): {len(anomalies)}")
    if anomalies:
        worst = max(anomalies, key=lambda x: x.score)
        print(f"  Pior anomalia: {worst.value:.1f}% às {worst.timestamp.strftime('%H:%M')} (z={worst.score:.2f})")

    # ──────────────────────────────────────────────────────────────────
    # BLOCO 3 — AULA 3: Investigação com IA
    # ──────────────────────────────────────────────────────────────────
    section("BLOCO 3/5 — AULA 3: Investigação assistida por IA")

    patterns = extract_patterns_local(SAMPLE_LOGS)
    print(f"\n  Padrões de log detectados: {len(patterns)}")
    for p in patterns[:3]:
        print(f"  [{p.pattern_type}] x{p.frequency}: {p.sample[:55]}")

    changes, incident = build_scenario()
    correlations = correlate_changes_with_incident(changes, incident)
    top_change = correlations[0] if correlations else None
    if top_change:
        print(f"\n  Mudança mais correlacionada: {top_change.change.change_id}")
        print(f"  Score: {top_change.correlation_score:.0%} → {top_change.verdict}")

    topology_ctx = topology_to_prompt_context(TOPOLOGY)
    print(f"\n  Contexto de topologia serializado: {len(topology_ctx)} chars")

    # ──────────────────────────────────────────────────────────────────
    # BLOCO 4 — AULA 4: Remediação automatizada
    # ──────────────────────────────────────────────────────────────────
    section("BLOCO 4/5 — AULA 4: Remediação automatizada com guardrails")

    guardrail_engine = GuardrailEngine()
    automation_request = AutomationRequest(
        "AUTO-FINAL", "increase_connection_pool", "database", "prod",
        estimated_blast_radius=0, is_reversible=True, risk_level="LOW",
        requested_by="self-healing-engine",
        description="Aumentar max_connections de 100 para 200 (temporário)",
    )
    result = guardrail_engine.process_request(automation_request)

    if result:
        runbook = create_auth_service_recovery_runbook()
        runbook.execute()

    # ──────────────────────────────────────────────────────────────────
    # BLOCO 5 — AULA 5: Pipeline integrado + documentação
    # ──────────────────────────────────────────────────────────────────
    section("BLOCO 5/5 — AULA 5: Pipeline integrado e documentação automática")

    pipeline = UnifiedOperationsPipeline("INC-2024-FINAL-001")
    pipeline.run()

    # ──────────────────────────────────────────────────────────────────
    # Conclusão do curso
    # ──────────────────────────────────────────────────────────────────
    total = (datetime.now() - t_start).total_seconds()

    print("\n" + "=" * 65)
    print("🎓 PARABÉNS! CURSO CONCLUÍDO COM SUCESSO!")
    print("=" * 65)
    print(f"""
  Você executou o fluxo completo de AIOps em {total:.1f}s:

  ✔ [Aula 1] Correlação de sinais → redução de alert storm
  ✔ [Aula 2] Baseline dinâmico → anomalia detectada com precisão
  ✔ [Aula 3] LLM + change correlation → causa raiz identificada
  ✔ [Aula 4] Guardrails + runbook → remediação segura e automática
  ✔ [Aula 5] Pipeline integrado → observabilidade → resolução

  ─────────────────────────────────────────────────────────────
  Próximos passos sugeridos:
  1. Implemente o alert correlator no seu ambiente de staging
  2. Configure baselines dinâmicos em pelo menos 3 métricas críticas
  3. Crie o primeiro runbook-as-code para o incidente mais recorrente
  4. Defina seus guardrails antes de ativar qualquer self-healing

  "AIOps não é sobre remover humanos das operações.
   É sobre dar superpoderes para os humanos que já estão lá."
  ─────────────────────────────────────────────────────────────
    """)


if __name__ == "__main__":
    run_complete_flow()
