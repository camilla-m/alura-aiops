"""
Vídeo 5.5 — Hands-on: Operação assistida por observabilidade inteligente
==========================================================================
EXERCÍCIO PRÁTICO FINAL — Aula 5 / Curso 3

Neste hands-on final você vai simular uma crise end-to-end
combinando TODAS as técnicas das 5 aulas:
  Aula 1: Observabilidade moderna e correlação de sinais
  Aula 2: Análise de tendências e previsão
  Aula 3: Alertas inteligentes e redução de ruído
  Aula 4: Investigação com IA e logs
  Aula 5: Operações centralizadas e decisão

Cenário:
  Sexta-feira 17:45 — pior horário possível.
  Múltiplos alertas disparam simultaneamente.
  Seu time tem 30 minutos para mitigar antes do pico de tráfego.

Execute:
  python crisis_simulation_lab.py
"""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class CrisisPhase(str, Enum):
    DETECTION = "DETECÇÃO"
    TRIAGE = "TRIAGEM"
    INVESTIGATION = "INVESTIGAÇÃO"
    MITIGATION = "MITIGAÇÃO"
    VERIFICATION = "VERIFICAÇÃO"


@dataclass
class CrisisSignal:
    timestamp: datetime
    source: str
    service: str
    message: str
    severity: str
    is_noise: bool = False
    correlation_id: str = ""


@dataclass
class InvestigationStep:
    phase: CrisisPhase
    action: str
    finding: str
    technique: str  # Qual aula/técnica usou
    duration_seconds: int


def generate_crisis() -> list[CrisisSignal]:
    """Gera cenário de crise com sinais reais e ruído."""
    base = datetime(2024, 9, 6, 17, 45, 0)
    corr = "crisis-2024-0906"

    signals = [
        # CAUSA RAIZ: DNS resolver configurado incorretamente após manutenção de rede
        CrisisSignal(base, "network-ops", "dns-resolver", "DNS resolver primary failover to secondary (maintenance completed)", "INFO", correlation_id=corr),

        # Sinais em cascata (reais)
        CrisisSignal(base + timedelta(seconds=30), "monitoring", "api-gateway", "DNS resolution timeout for auth-service.internal (5000ms)", "ERROR", correlation_id=corr),
        CrisisSignal(base + timedelta(seconds=45), "monitoring", "auth-service", "Connection refused from api-gateway (DNS resolution failed)", "ERROR", correlation_id=corr),
        CrisisSignal(base + timedelta(minutes=1), "alerting", "checkout-service", "SLO breach: availability < 99.9% for 5 minutes", "CRITICAL", correlation_id=corr),
        CrisisSignal(base + timedelta(minutes=1, seconds=15), "monitoring", "payment-service", "Upstream auth-service unhealthy — circuit breaker OPEN", "ERROR", correlation_id=corr),
        CrisisSignal(base + timedelta(minutes=2), "monitoring", "api-gateway", "Error rate 23% (baseline: 0.1%)", "CRITICAL", correlation_id=corr),
        CrisisSignal(base + timedelta(minutes=2, seconds=30), "logs", "auth-service", "java.net.UnknownHostException: database.internal", "ERROR", correlation_id=corr),
        CrisisSignal(base + timedelta(minutes=3), "infra", "dns-resolver", "Query failure rate: 45% (secondary resolver overloaded)", "ERROR", correlation_id=corr),

        # RUÍDO (sinais válidos mas não relevantes agora)
        CrisisSignal(base + timedelta(seconds=20), "monitoring", "analytics", "ETL job completed: 12,450 records processed", "INFO", is_noise=True),
        CrisisSignal(base + timedelta(seconds=40), "alerting", "notification-svc", "Email queue depth: 234 (normal range)", "INFO", is_noise=True),
        CrisisSignal(base + timedelta(minutes=1, seconds=30), "infra", "cdn", "Cache hit ratio: 94.2% (healthy)", "INFO", is_noise=True),
        CrisisSignal(base + timedelta(minutes=2), "monitoring", "search-service", "CPU utilization: 62% (normal for Friday peak)", "INFO", is_noise=True),
        CrisisSignal(base + timedelta(minutes=2, seconds=45), "alerting", "product-service", "Memory usage 78% (approaching threshold)", "WARN", is_noise=True),
        CrisisSignal(base + timedelta(minutes=3, seconds=15), "logs", "analytics", "Slow query: report_generator took 3200ms", "WARN", is_noise=True),
        CrisisSignal(base + timedelta(minutes=3, seconds=30), "infra", "k8s-cluster", "Node auto-scaling: 3 → 4 nodes (scheduled)", "INFO", is_noise=True),
        CrisisSignal(base + timedelta(minutes=4), "monitoring", "log-collector", "Log volume: 45,000 lines/min (normal)", "INFO", is_noise=True),
    ]

    return sorted(signals, key=lambda s: s.timestamp)


def run_crisis_simulation() -> None:
    print("=" * 70)
    print("🚨 HANDS-ON FINAL: Simulação de Crise End-to-End")
    print("   Curso 3 — Observabilidade Inteligente")
    print("=" * 70)
    print(f"\n  ⏰ Sexta-feira 17:45 — Pico de tráfego em 30 minutos")
    print(f"  📱 Múltiplos alertas disparando simultaneamente")
    print(f"  🎯 Missão: Mitigar antes do pico\n")
    time.sleep(0.5)

    signals = generate_crisis()

    # === FASE 1: DETECÇÃO ===
    print(f"{'═' * 70}")
    print(f"  📡 FASE 1: DETECÇÃO (Aula 1 — Observabilidade moderna)")
    print(f"{'═' * 70}")
    print(f"\n  {len(signals)} sinais recebidos no hub centralizado:\n")

    for s in signals:
        sev_icon = {"INFO": "  ", "WARN": "⚠️", "ERROR": "❌", "CRITICAL": "🔴"}[s.severity]
        noise = " [NOISE]" if s.is_noise else ""
        print(f"  {sev_icon} [{s.timestamp.strftime('%H:%M:%S')}] {s.source}/{s.service}: "
              f"{s.message[:55]}...{noise}")
    time.sleep(0.3)

    # === FASE 2: TRIAGEM ===
    print(f"\n{'═' * 70}")
    print(f"  🔍 FASE 2: TRIAGEM (Aula 3 — Redução de ruído)")
    print(f"{'═' * 70}")

    real_signals = [s for s in signals if not s.is_noise]
    noise_signals = [s for s in signals if s.is_noise]

    print(f"\n  Aplicando noise gate e filtragem contextual...")
    print(f"  Sinais reais    : {len(real_signals)} (correlacionados)")
    print(f"  Ruído filtrado  : {len(noise_signals)} sinais irrelevantes")
    print(f"  Redução         : {len(noise_signals)/len(signals)*100:.0f}%\n")

    print(f"  Sinais relevantes (pós-filtro):")
    for s in real_signals:
        sev_icon = {"INFO": "  ", "WARN": "⚠️", "ERROR": "❌", "CRITICAL": "🔴"}[s.severity]
        print(f"  {sev_icon} [{s.timestamp.strftime('%H:%M:%S')}] {s.service}: {s.message[:60]}...")
    time.sleep(0.3)

    # === FASE 3: INVESTIGAÇÃO ===
    print(f"\n{'═' * 70}")
    print(f"  🔬 FASE 3: INVESTIGAÇÃO (Aulas 1, 2, 4 — Correlação + IA)")
    print(f"{'═' * 70}")

    steps = [
        InvestigationStep(CrisisPhase.INVESTIGATION,
            "Correlacionar sinais por timestamp e dependência",
            "Todos os erros começam ~30s após 'DNS resolver failover'",
            "Aula 1.2 — Correlação de sinais", 60),
        InvestigationStep(CrisisPhase.INVESTIGATION,
            "Verificar contexto operacional (mudanças recentes)",
            "Manutenção de rede completada às 17:45 — DNS failover",
            "Aula 1.3 — Contexto operacional", 45),
        InvestigationStep(CrisisPhase.INVESTIGATION,
            "Clustering de logs de erro por padrão",
            "86% dos erros são 'UnknownHostException' → DNS resolution",
            "Aula 4.3 — Log clustering", 30),
        InvestigationStep(CrisisPhase.INVESTIGATION,
            "Verificar trace do fluxo de checkout",
            "Trace mostra: gateway → auth (DNS fail) → cascata",
            "Aula 1.2 — Traces distribuídos", 45),
        InvestigationStep(CrisisPhase.INVESTIGATION,
            "Hipótese: DNS secondary está sobrecarregado pós-failover",
            "Confirmado: DNS query failure rate = 45%",
            "Aula 5.4 — Hypothesis-driven", 30),
    ]

    for step in steps:
        print(f"\n  🔬 Ação: {step.action}")
        print(f"     Achado: {step.finding}")
        print(f"     Técnica: {step.technique}")
    time.sleep(0.3)

    # === FASE 4: DIAGNÓSTICO ===
    print(f"\n{'═' * 70}")
    print(f"  🎯 DIAGNÓSTICO (consolidação)")
    print(f"{'═' * 70}")
    print(f"""
  CAUSA RAIZ IDENTIFICADA:
  ─────────────────────────────────────────────
  A manutenção de rede às 17:45 fez failover do DNS resolver
  primário para o secundário. O resolver secundário não suporta
  a carga total do cluster (dimensionado apenas para 30% do tráfego).

  CADEIA DE CAUSALIDADE:
  ─────────────────────────────────────────────
  1. Manutenção rede → DNS failover para secondary
  2. DNS secondary sobrecarregado → 45% query failures
  3. Serviços não resolvem nomes internos → connection refused
  4. auth-service DOWN → circuit breakers abrem em cascata
  5. checkout/payment degradados → SLO breach

  IMPACTO (Aula 5.2 — linguagem de negócios):
  ─────────────────────────────────────────────
  Checkout indisponível para ~23% dos usuários
  Revenue at risk: ~R$ 8.400/hora (Friday peak incoming)
    """)
    time.sleep(0.3)

    # === FASE 5: MITIGAÇÃO ===
    print(f"{'═' * 70}")
    print(f"  🔧 FASE 5: MITIGAÇÃO")
    print(f"{'═' * 70}")
    print(f"""
  ✅ AÇÕES EXECUTADAS:
  ─────────────────────────────────────────────
  1. [17:52] Reativação manual do DNS resolver primário
  2. [17:54] Flush de DNS cache em todos os pods do cluster
  3. [17:55] Reset de circuit breakers em auth-service
  4. [17:57] Verificação: DNS query success rate voltando a 99.8%
    """)
    time.sleep(0.3)

    # === FASE 6: VERIFICAÇÃO ===
    print(f"{'═' * 70}")
    print(f"  ✅ FASE 6: VERIFICAÇÃO")
    print(f"{'═' * 70}")
    print(f"""
  Métricas pós-mitigação (18:00):
  ─────────────────────────────────────────────
  DNS resolution   : 99.9% success ✅
  auth-service     : error_rate 0.02% ✅
  checkout-service : error_rate 0.08% ✅
  SLO compliance   : recovering (estimated full recovery: 18:15) ✅
  Circuit breakers : all CLOSED ✅

  ⏱️  Timeline final:
  17:45 — Incidente inicia (DNS failover)
  17:46 — Primeira detecção (alertas)
  17:48 — Triagem concluída (ruído filtrado)
  17:52 — Causa raiz identificada (7 min!)
  17:57 — Mitigação concluída (12 min total!)
  18:00 — Sistema recuperado ✅
    """)

    # === RELATÓRIO FINAL ===
    print(f"{'═' * 70}")
    print("📋 RELATÓRIO FINAL DO EXERCÍCIO")
    print(f"{'═' * 70}")

    total_signals = len(signals)
    real = len(real_signals)
    noise = len(noise_signals)
    total_time = sum(s.duration_seconds for s in steps)

    print(f"""
  📊 MÉTRICAS DE PERFORMANCE:
  ─────────────────────────────────────────────
  Sinais recebidos       : {total_signals}
  Sinais relevantes      : {real} ({real/total_signals*100:.0f}%)
  Ruído filtrado         : {noise} ({noise/total_signals*100:.0f}%)
  Tempo de investigação  : {total_time // 60}min {total_time % 60}s
  TTD (time to detect)   : 1 minuto
  TTI (time to identify) : 7 minutos
  TTM (time to mitigate) : 12 minutos
  TTR (time to recover)  : 15 minutos

  🧰 TÉCNICAS DO CURSO UTILIZADAS:
  ─────────────────────────────────────────────
  ✔ Aula 1: Correlação de sinais + traces + contexto operacional
  ✔ Aula 2: Baseline para identificar que DNS failure rate é anômalo
  ✔ Aula 3: Noise gate filtrou {noise} sinais irrelevantes
  ✔ Aula 4: Log clustering isolou padrão 'UnknownHostException'
  ✔ Aula 5: Hub centralizado + hipótese dirigida + carga cognitiva
    """)

    print("=" * 70)
    print("🎓 CURSO 3 CONCLUÍDO — OBSERVABILIDADE INTELIGENTE!")
    print("=" * 70)
    print("""
  Parabéns! Você completou o Curso 3 — Observabilidade Inteligente.

  Habilidades adquiridas:
  ─────────────────────────────────────────────
  ✔ Observabilidade moderna com OpenTelemetry
  ✔ Análise de tendências e previsão de saturação
  ✔ Alertas inteligentes com baselines dinâmicos
  ✔ Investigação de logs com IA e clustering
  ✔ Operações centralizadas sob pressão

  "A diferença entre um SRE e um administrador de sistemas é que
   o SRE usa DADOS para tomar decisões sob pressão, não intuição."
    """)


if __name__ == "__main__":
    run_crisis_simulation()
