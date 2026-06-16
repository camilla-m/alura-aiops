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

import importlib.util
import sys
import time
from datetime import datetime
from pathlib import Path


def _load(module_name: str, file_path: Path):
    """Carrega um módulo Python pelo caminho absoluto (contorna nomes com hífens)."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


# Raiz do projeto (2 níveis acima deste arquivo)
_ROOT = Path(__file__).parent.parent.parent

# ── Aula 1 ────────────────────────────────────────────────────────────────
_a1_storm   = _load("alert_storm_demo",  _ROOT / "aula-01-volume-de-sinais" / "video-1.1-alert-storm"            / "alert_storm_demo.py")
_a1_corr    = _load("event_correlator",  _ROOT / "aula-01-volume-de-sinais" / "video-1.2-correlacao-incidentes"  / "event_correlator.py")
_a1_score   = _load("impact_scorer",     _ROOT / "aula-01-volume-de-sinais" / "video-1.3-priorizacao"            / "impact_scorer.py")

simulate_alert_storm  = _a1_storm.simulate_alert_storm
analyze_alert_storm   = _a1_storm.analyze_alert_storm
EventCorrelator       = _a1_corr.EventCorrelator
Signal                = _a1_corr.Signal
SignalType            = _a1_corr.SignalType
calculate_impact_score = _a1_score.calculate_impact_score

# ── Aula 2 ────────────────────────────────────────────────────────────────
_a2_anom    = _load("anomaly_detector",  _ROOT / "aula-02-deteccao-de-anomalias" / "video-2.1-anomalias-infra"      / "anomaly_detector.py")
_a2_base    = _load("dynamic_baseline",  _ROOT / "aula-02-deteccao-de-anomalias" / "video-2.2-baselines-dinamicos"  / "dynamic_baseline.py")

generate_cpu_series   = _a2_anom.generate_cpu_series
detect_by_zscore      = _a2_anom.detect_by_zscore
DynamicBaseline       = _a2_base.DynamicBaseline
generate_weekly_metric = _a2_base.generate_weekly_metric

# ── Aula 3 ────────────────────────────────────────────────────────────────
_a3_log     = _load("log_analyzer_ai",   _ROOT / "aula-03-investigacao-assistida-ia" / "video-3.2-analise-logs"         / "log_analyzer_ai.py")
_a3_change  = _load("change_correlator", _ROOT / "aula-03-investigacao-assistida-ia" / "video-3.3-mudancas-incidentes"  / "change_correlator.py")
_a3_topo    = _load("topology_context",  _ROOT / "aula-03-investigacao-assistida-ia" / "video-3.4-contexto-distribuido" / "topology_context.py")

SAMPLE_LOGS                    = _a3_log.SAMPLE_LOGS
extract_patterns_local         = _a3_log.extract_patterns_local
build_scenario                 = _a3_change.build_scenario
correlate_changes_with_incident = _a3_change.correlate_changes_with_incident
TOPOLOGY                       = _a3_topo.TOPOLOGY
topology_to_prompt_context     = _a3_topo.topology_to_prompt_context

# ── Aula 4 ────────────────────────────────────────────────────────────────
_a4_run     = _load("runbook_executor",  _ROOT / "aula-04-automacao-e-resposta" / "video-4.2-runbooks"   / "runbook_executor.py")
_a4_guard   = _load("guardrail_engine",  _ROOT / "aula-04-automacao-e-resposta" / "video-4.4-guardrails" / "guardrail_engine.py")

create_auth_service_recovery_runbook = _a4_run.create_auth_service_recovery_runbook
GuardrailEngine    = _a4_guard.GuardrailEngine
AutomationRequest  = _a4_guard.AutomationRequest

# ── Aula 5 ────────────────────────────────────────────────────────────────
_a5_pipe    = _load("unified_pipeline",  _ROOT / "aula-05-operacoes-resilientes" / "video-5.2-fluxos-integrados" / "unified_pipeline.py")
_a5_doc     = _load("ai_documentation",  _ROOT / "aula-05-operacoes-resilientes" / "video-5.3-ia-workflow"       / "ai_documentation.py")

UnifiedOperationsPipeline       = _a5_pipe.UnifiedOperationsPipeline
IncidentData                    = _a5_doc.IncidentData
generate_postmortem_with_ai_prompt = _a5_doc.generate_postmortem_with_ai_prompt


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
