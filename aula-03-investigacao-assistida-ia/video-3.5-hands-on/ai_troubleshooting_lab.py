"""
Vídeo 3.5 — Hands-on: Troubleshooting assistido por IA
========================================================
EXERCÍCIO PRÁTICO — Aula 3

Resolve um cenário real de indisponibilidade de microsserviço
correlacionando logs, telemetria e topologia via IA.

Fluxo do exercício:
  1. Carrega o incidente e seus sinais
  2. Analisa logs com extração de padrões
  3. Correlaciona mudanças recentes
  4. Constrói o contexto de topologia
  5. Gera o prompt unificado para investigação com IA
  6. Apresenta o resultado final estruturado

Execute:
  python ai_troubleshooting_lab.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from video_3_2_analise_logs.log_analyzer_ai import (
    SAMPLE_LOGS, extract_patterns_local, chunk_logs, build_log_analysis_prompt,
)
from video_3_3_mudancas_incidentes.change_correlator import (
    build_scenario, correlate_changes_with_incident,
)
from video_3_4_contexto_distribuido.topology_context import (
    TOPOLOGY, topology_to_prompt_context,
)


def build_unified_investigation_prompt(
    log_patterns: list,
    top_change,
    topology_ctx: str,
    incident_title: str,
) -> str:
    """Constrói o prompt unificado combinando todos os contextos."""
    patterns_text = "\n".join(
        f"  [{p.pattern_type}] x{p.frequency}: {p.sample[:60]}"
        for p in log_patterns[:5]
    )

    change_text = (
        f"{top_change.change.change_id} — {top_change.change.description}\n"
        f"  Serviço: {top_change.change.service} | Score: {top_change.correlation_score:.0%}"
        if top_change else "Nenhuma mudança correlacionada"
    )

    return f"""Você é um SRE sênior conduzindo um Root Cause Analysis (RCA).

INCIDENTE: {incident_title}

PADRÕES DE LOG IDENTIFICADOS:
{patterns_text}

MUDANÇA MAIS CORRELACIONADA:
{change_text}

{topology_ctx}

TAREFA — Root Cause Analysis:
1. Identifique a causa raiz mais provável com base nos 3 contextos acima
2. Descreva o caminho de propagação da falha (serviço A → B → C → usuário)
3. Recomende as 3 ações imediatas de remediação
4. Sugira 2 melhorias preventivas para evitar reocorrência

Seja objetivo e fundamentado nos dados fornecidos.
"""


def run_lab() -> None:
    print("=" * 65)
    print("🧪 LABORATÓRIO: Troubleshooting Assistido por IA")
    print("   Nível 1 — AIOps & Automação de Incidentes")
    print("=" * 65)

    incident_title = "Frontend retornando 503 — auth-service degradado (09:02 UTC)"

    # PASSO 1
    print("\n── PASSO 1/4: Extraindo padrões dos logs ──────────────────")
    patterns = extract_patterns_local(SAMPLE_LOGS)
    print(f"  {len(SAMPLE_LOGS)} linhas analisadas → {len(patterns)} padrões detectados")
    for p in patterns[:3]:
        print(f"  [{p.pattern_type}] x{p.frequency}: {p.sample[:55]}")
    time.sleep(0.5)

    # PASSO 2
    print("\n── PASSO 2/4: Correlacionando mudanças recentes ───────────")
    changes, incident = build_scenario()
    correlations = correlate_changes_with_incident(changes, incident)
    top = correlations[0] if correlations else None
    if top:
        print(f"  Mudança mais provável: [{top.change.change_id}] {top.change.description[:50]}")
        print(f"  Score de correlação: {top.correlation_score:.0%} | {top.verdict}")
    time.sleep(0.5)

    # PASSO 3
    print("\n── PASSO 3/4: Construindo contexto de topologia ───────────")
    degraded = [n for n in TOPOLOGY.values() if n.health != "healthy"]
    print(f"  {len(TOPOLOGY)} serviços no grafo | {len(degraded)} degradados/down")
    topology_ctx = topology_to_prompt_context(TOPOLOGY, focus_services=[n.name for n in degraded])
    print(f"  Contexto serializado: {len(topology_ctx)} chars")
    time.sleep(0.5)

    # PASSO 4
    print("\n── PASSO 4/4: Gerando prompt unificado para IA ────────────")
    prompt = build_unified_investigation_prompt(patterns, top, topology_ctx, incident_title)
    print(f"  Prompt gerado: {len(prompt)} chars (~{len(prompt)//4} tokens)\n")

    print("─" * 65)
    print("PROMPT FINAL (enviado ao LLM):")
    print("─" * 65)
    print(prompt)

    print("\n" + "=" * 65)
    print("📋 RESULTADO ESPERADO DA IA (resumo)")
    print("=" * 65)
    print("""
  Causa raiz identificada:
  → Deploy auth-service v2.3.1 (CHG-001, 17 min antes do incidente)
    introduziu novo driver PostgreSQL que não respeita o max_connections,
    esgotando o connection pool e causando falha em cascata.

  Caminho de propagação:
  → postgresql-primary (pool esgotado)
    → auth-service (89% erros) → api-gateway (503) → frontend
    → payment-service (100% erros) → cart-service (38% erros)

  Ações imediatas:
  1. Rollback auth-service para v2.3.0
  2. Aumentar max_connections temporariamente para 200
  3. Reiniciar auth-service pods para liberar conexões presas

  Preventivas:
  1. Configurar PgBouncer para connection pooling externo
  2. Adicionar teste de carga no pipeline de deploy do auth-service
    """)

    print("=" * 65)
    print("🎓 FIM DO HANDS-ON — AULA 3 CONCLUÍDA!")
    print("=" * 65)
    print("""
  Você aprendeu a:
  ✔ Formular prompts eficazes para diagnóstico de incidentes
  ✔ Analisar logs com extração de padrões
  ✔ Correlacionar mudanças com incidentes
  ✔ Serializar topologia de serviços para contexto de LLM
  ✔ Integrar múltiplos contextos em um prompt unificado

  Próxima aula: Automação operacional e resposta a incidentes →
    """)


if __name__ == "__main__":
    run_lab()
