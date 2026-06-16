"""
Vídeo 1.5 — Hands-on: Investigando incidentes com múltiplos sinais
===================================================================
EXERCÍCIO PRÁTICO — Aula 1

Neste hands-on você vai simular a investigação de um incidente real
combinando todas as técnicas aprendidas na Aula 1:
  1. Identificar o alert storm
  2. Correlacionar os sinais automaticamente
  3. Calcular o impact score
  4. Gerar o relatório de triagem final

Cenário:
  Uma segunda-feira às 09:02 UTC, o time de plantão recebe 23 alertas
  simultâneos. Sua missão é isolá-los em incidentes distintos,
  identificar a causa raiz e recomendar as ações corretas.

Execute:
  python incident_investigation.py
"""

import importlib.util
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def _load(module_name: str, file_path: Path):
    """Carrega um módulo Python pelo caminho absoluto (contorna nomes com hífens)."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


_BASE = Path(__file__).parent.parent

_alert_storm    = _load("alert_storm_demo",  _BASE / "video-1.1-alert-storm"    / "alert_storm_demo.py")
_correlator_mod = _load("event_correlator",  _BASE / "video-1.2-correlacao-incidentes" / "event_correlator.py")
_scorer_mod     = _load("impact_scorer",     _BASE / "video-1.3-priorizacao"    / "impact_scorer.py")

Alert      = _alert_storm.Alert
Severity   = _alert_storm.Severity
EventCorrelator = _correlator_mod.EventCorrelator
Signal          = _correlator_mod.Signal
SignalType      = _correlator_mod.SignalType
calculate_impact_score = _scorer_mod.calculate_impact_score
print_triage_report    = _scorer_mod.print_triage_report


# ---------------------------------------------------------------------------
# Cenário do exercício: dados do incidente
# ---------------------------------------------------------------------------

def load_incident_scenario() -> list[dict[str, Any]]:
    """
    Carrega os sinais do incidente simulado.
    Em um ambiente real, esses dados viriam de Elasticsearch, Datadog, etc.
    """
    base_time = datetime(2024, 6, 3, 9, 2, 0)  # Segunda-feira, 09:02 UTC

    scenario: list[dict] = [
        # === INCIDENTE 1: Falha de database ===
        {"type": "LOG",    "service": "database",        "t": 0,  "msg": "FATAL: max_connections=100 reached", "trace": "t-db-001"},
        {"type": "METRIC", "service": "database",        "t": 5,  "msg": "connections_active=100", "value": 100.0},
        {"type": "LOG",    "service": "cache",           "t": 10, "msg": "ERROR: Redis fallback to DB failed", "trace": "t-db-001"},
        {"type": "LOG",    "service": "auth-service",    "t": 15, "msg": "ERROR: DB auth query timeout after 30s", "trace": "t-db-001"},
        {"type": "METRIC", "service": "auth-service",    "t": 18, "msg": "error_rate=0.97", "value": 0.97},
        {"type": "LOG",    "service": "api-gateway",     "t": 20, "msg": "ERROR: upstream auth-service 503", "trace": "t-db-001"},
        {"type": "METRIC", "service": "api-gateway",     "t": 22, "msg": "latency_p99=12000ms", "value": 12000.0},
        {"type": "LOG",    "service": "frontend",        "t": 25, "msg": "WARN: Returning 503 to end users"},
        {"type": "LOG",    "service": "payment-service", "t": 28, "msg": "ERROR: Cannot process payment - auth unavailable"},
        {"type": "LOG",    "service": "cart-service",    "t": 30, "msg": "ERROR: Cart checkout blocked by auth failure"},

        # === INCIDENTE 2: Problema de deployment isolado ===
        {"type": "LOG",    "service": "analytics",       "t": 180, "msg": "INFO: Schema migration completed — analytics v2.1"},
        {"type": "LOG",    "service": "analytics",       "t": 182, "msg": "WARN: analytics job slow (expected post-migration)"},
        {"type": "METRIC", "service": "analytics",       "t": 185, "msg": "job_duration_seconds=450", "value": 450.0},

        # === Ruído / eventos normais ===
        {"type": "LOG",    "service": "notification-service", "t": 300, "msg": "INFO: Email batch job completed successfully"},
        {"type": "METRIC", "service": "notification-service", "t": 305, "msg": "emails_sent=1247", "value": 1247.0},
    ]

    # Converte para objetos Signal
    signals: list[Signal] = []
    for item in scenario:
        signals.append(Signal(
            signal_type=SignalType[item["type"]],
            service=item["service"],
            timestamp=base_time + timedelta(seconds=item["t"]),
            message=item["msg"],
            trace_id=item.get("trace"),
            value=item.get("value"),
        ))
    return signals


# ---------------------------------------------------------------------------
# Pipeline completo de investigação
# ---------------------------------------------------------------------------

def run_investigation() -> None:
    print("=" * 65)
    print("🚨 ALERTA: Incidente detectado — Segunda-feira 09:02 UTC")
    print("=" * 65)
    print(f"\n  Time de plantão acionado. Analisando sinais...\n")
    time.sleep(0.5)

    # PASSO 1: Carregar sinais do incidente
    signals = load_incident_scenario()
    print(f"  📥 {len(signals)} sinais recebidos de múltiplas fontes")
    print(f"  (logs, métricas e traces misturados)\n")
    time.sleep(0.5)

    # PASSO 2: Correlação automática
    print("─" * 65)
    print("PASSO 1/3 — Correlacionando sinais automaticamente")
    print("─" * 65)
    correlator = EventCorrelator(time_window_seconds=120)
    for s in signals:
        correlator.ingest(s)
    correlator.report()
    time.sleep(0.5)

    # PASSO 3: Impact scoring dos serviços afetados
    print("\n" + "─" * 65)
    print("PASSO 2/3 — Calculando impact score dos serviços afetados")
    print("─" * 65)

    # Pega o incidente maior para triagem
    incidents = correlator.get_incidents()
    main_incident = incidents[0]
    affected_services = list(main_incident.affected_services)

    triages = [calculate_impact_score(s) for s in affected_services if s in [
        "database", "auth-service", "api-gateway", "payment-service"
    ]]
    triages.sort(key=lambda t: t.impact_score, reverse=True)
    print_triage_report(triages)

    # PASSO 4: Relatório final
    print("\n" + "=" * 65)
    print("PASSO 3/3 — RELATÓRIO FINAL DE INVESTIGAÇÃO")
    print("=" * 65)

    top = triages[0] if triages else None
    print(f"""
  📋 SUMÁRIO DO INCIDENTE
  ─────────────────────────────────────────────
  Início detectado : 09:02 UTC
  Sinais recebidos : {len(signals)} (logs + métricas + traces)
  Incidentes únicos: {len(incidents)} agrupados pelo correlator

  🎯 CAUSA RAIZ IDENTIFICADA
  ─────────────────────────────────────────────
  Serviço    : database
  Problema   : Connection pool esgotado (max_connections=100)
  Impacto    : Cascata em auth, api-gateway, payment, cart, frontend
  Score      : {top.impact_score if top else 'N/A'}/100  → {top.priority if top else ''}

  ✅ AÇÕES RECOMENDADAS (em ordem de prioridade)
  ─────────────────────────────────────────────
  1. [IMEDIATO]  Aumentar max_connections ou reiniciar pool
  2. [IMEDIATO]  Verificar se há query lenta travando conexões (pg_stat_activity)
  3. [CURTO]     Configurar PgBouncer para connection pooling externo
  4. [MÉDIO]     Revisar limite de conexões por serviço (least-privilege)
  5. [LONGO]     Configurar alerta de baseline dinâmico em connections_active

  📊 MÉTRICAS DO EXERCÍCIO
  ─────────────────────────────────────────────
  Redução de ruído  : {len(signals) - len(incidents)} sinais agrupados ({(len(signals)-len(incidents))/len(signals)*100:.0f}% de redução)
  Tempo de triagem  : ~2 min (vs. 30+ min manualmente)
  MTTR estimado     : 8-15 min com automação vs. 45-90 min manual
    """)

    print("=" * 65)
    print("🎓 FIM DO HANDS-ON — AULA 1 CONCLUÍDA!")
    print("=" * 65)
    print("""
  Você aprendeu a:
  ✔ Identificar alert storms e seu impacto operacional
  ✔ Correlacionar sinais automaticamente por tempo e topologia
  ✔ Calcular o impact score para priorização inteligente
  ✔ Gerar relatórios de triagem estruturados

  Próxima aula: Detecção de anomalias com baselines dinâmicos →
    """)


if __name__ == "__main__":
    run_investigation()
