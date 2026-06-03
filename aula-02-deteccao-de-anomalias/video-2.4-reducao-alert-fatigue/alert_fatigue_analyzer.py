"""
Vídeo 2.4 — Redução de alert fatigue
=====================================
Demonstra estratégias para identificar e eliminar alertas
desnecessários que contribuem para a fadiga operacional.

Conceitos demonstrados:
- Análise de volume e qualidade de alertas existentes
- Detecção de alertas de baixa qualidade (muito frequentes, sem ação)
- Estratégias de consolidação e deduplicação
- Métricas de saúde do sistema de alertas (Signal-to-Noise Ratio)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from statistics import mean
from typing import Optional


@dataclass
class AlertRecord:
    """Registro histórico de um alerta."""
    alert_id: str
    rule_name: str
    service: str
    fired_at: datetime
    resolved_at: Optional[datetime]
    acknowledged: bool
    action_taken: bool  # se alguém agiu sobre este alerta
    severity: str


@dataclass
class AlertRuleAnalysis:
    """Análise de qualidade de uma regra de alerta."""
    rule_name: str
    service: str
    total_fires: int
    action_rate: float        # % de alertas que geraram ação real
    avg_duration_min: float   # duração média em minutos
    fires_per_day: float
    signal_to_noise: float    # SNR (0-1): 1 = todos acionáveis
    recommendation: str
    priority_to_fix: str      # HIGH | MEDIUM | LOW


# ---------------------------------------------------------------------------
# Gerador de dados históricos de alertas
# ---------------------------------------------------------------------------

ALERT_RULES = [
    # Regras de alta qualidade (poucas disparadas, sempre acionadas)
    ("db_connection_pool_critical", "database",    "CRITICAL"),
    ("payment_error_rate_spike",    "payment-svc", "CRITICAL"),

    # Regras de qualidade média
    ("cpu_sustained_high",          "api-gateway", "HIGH"),
    ("memory_near_limit",           "worker-svc",  "MEDIUM"),

    # Regras de baixa qualidade (muitas disparadas, raramente acionadas)
    ("cpu_brief_spike",             "frontend",    "LOW"),
    ("healthcheck_flap",            "cache",       "LOW"),
    ("disk_minor_fluctuation",      "database",    "LOW"),
    ("response_time_micro_spike",   "api-gateway", "LOW"),
]


def generate_alert_history(days: int = 30) -> list[AlertRecord]:
    """Gera histórico de alertas com diferentes padrões de qualidade."""
    records = []
    base_date = datetime.now() - timedelta(days=days)
    alert_counter = 0

    for rule_name, service, severity in ALERT_RULES:
        # Define padrão de disparo por qualidade
        if severity == "CRITICAL":
            fires_per_day = random.uniform(0.1, 0.5)
            action_prob = 0.95
        elif severity == "HIGH":
            fires_per_day = random.uniform(0.5, 2.0)
            action_prob = 0.75
        elif severity == "MEDIUM":
            fires_per_day = random.uniform(2.0, 8.0)
            action_prob = 0.40
        else:  # LOW — alertas ruidosos
            fires_per_day = random.uniform(10.0, 50.0)
            action_prob = 0.05

        total_fires = int(fires_per_day * days)

        for _ in range(total_fires):
            alert_counter += 1
            fired_at = base_date + timedelta(
                seconds=random.randint(0, days * 86400)
            )
            duration = timedelta(minutes=random.uniform(2, 120))
            resolved_at = fired_at + duration

            records.append(AlertRecord(
                alert_id=f"ALT-{alert_counter:05d}",
                rule_name=rule_name,
                service=service,
                fired_at=fired_at,
                resolved_at=resolved_at,
                acknowledged=random.random() < 0.8,
                action_taken=random.random() < action_prob,
                severity=severity,
            ))

    return sorted(records, key=lambda r: r.fired_at)


def analyze_alert_quality(records: list[AlertRecord]) -> list[AlertRuleAnalysis]:
    """Analisa a qualidade de cada regra de alerta."""
    # Agrupa por regra
    by_rule: dict[str, list[AlertRecord]] = {}
    for r in records:
        by_rule.setdefault(r.rule_name, []).append(r)

    analyses = []
    total_days = 30

    for rule_name, rule_records in by_rule.items():
        service = rule_records[0].service
        total_fires = len(rule_records)
        action_rate = mean(1.0 if r.action_taken else 0.0 for r in rule_records)
        fires_per_day = total_fires / total_days

        durations = []
        for r in rule_records:
            if r.resolved_at:
                dur = (r.resolved_at - r.fired_at).total_seconds() / 60
                durations.append(dur)
        avg_duration = mean(durations) if durations else 0

        snr = action_rate  # simplificação: SNR = taxa de acionamento

        # Recomendação
        if snr < 0.1 and fires_per_day > 5:
            recommendation = "❌ ELIMINAR: alta frequência, nunca gera ação. Remover ou reclassificar como informativo."
            priority = "HIGH"
        elif snr < 0.3 and fires_per_day > 2:
            recommendation = "⚠️  CONSOLIDAR: muitos disparos, poucas ações. Aumentar threshold ou adicionar hysteresis."
            priority = "HIGH"
        elif snr < 0.6:
            recommendation = "🔧 REFINAR: action rate moderada. Revisar condições e adicionar contexto."
            priority = "MEDIUM"
        else:
            recommendation = "✅ MANTER: boa relação sinal/ruído."
            priority = "LOW"

        analyses.append(AlertRuleAnalysis(
            rule_name=rule_name, service=service,
            total_fires=total_fires, action_rate=action_rate,
            avg_duration_min=avg_duration, fires_per_day=fires_per_day,
            signal_to_noise=snr, recommendation=recommendation,
            priority_to_fix=priority,
        ))

    return sorted(analyses, key=lambda a: a.signal_to_noise)


def print_alert_health_report(analyses: list[AlertRuleAnalysis], total_records: int) -> None:
    total_high = sum(1 for a in analyses if a.priority_to_fix == "HIGH")
    noisy_fires = sum(a.total_fires for a in analyses if a.priority_to_fix == "HIGH")
    noise_pct = noisy_fires / total_records * 100 if total_records > 0 else 0

    print("\n" + "=" * 70)
    print("📊 RELATÓRIO DE SAÚDE DO SISTEMA DE ALERTAS")
    print("=" * 70)
    print(f"\n  Total de alertas (30 dias) : {total_records:,}")
    print(f"  Regras analisadas          : {len(analyses)}")
    print(f"  Regras com alta prioridade : {total_high}")
    print(f"  Alertas ruidosos (inúteis) : {noisy_fires:,} ({noise_pct:.0f}% do total)")

    print(f"\n  {'Regra':<35} {'SNR':>5} {'Disp/d':>7} {'Ação%':>6}  Prioridade")
    print("  " + "─" * 65)

    for a in analyses:
        snr_bar = "█" * int(a.signal_to_noise * 10)
        print(
            f"  {a.rule_name:<35} {a.signal_to_noise:>4.0%} "
            f"{a.fires_per_day:>7.1f} {a.action_rate:>5.0%}  {a.priority_to_fix}"
        )

    print(f"\n  {'─'*65}")
    print("\n  📋 RECOMENDAÇÕES DETALHADAS\n")
    for a in analyses:
        if a.priority_to_fix in ("HIGH", "MEDIUM"):
            print(f"  [{a.priority_to_fix}] {a.rule_name}")
            print(f"         {a.recommendation}")
            print()


if __name__ == "__main__":
    print("🔬 Demo: Redução de Alert Fatigue")
    print("     Nível 1 — AIOps & Automação de Incidentes\n")

    records = generate_alert_history(days=30)
    analyses = analyze_alert_quality(records)
    print_alert_health_report(analyses, len(records))
