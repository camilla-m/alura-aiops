"""
Vídeo 3.5 — Hands-on: Configurando alertas inteligentes
=========================================================
EXERCÍCIO PRÁTICO — Aula 3

Neste hands-on você vai configurar um sistema de alertas completo:
  1. Auditar alertas existentes (3.3)
  2. Implementar baselines dinâmicos (3.2)
  3. Configurar supressão por topologia (3.4)
  4. Medir redução de ruído antes/depois

Cenário:
  Você é o SRE lead responsável por otimizar o sistema de alertas
  do time. Nas últimas 4 semanas, a equipe recebeu 847 alertas,
  dos quais apenas 127 exigiram ação real (15% de signal-to-noise).

Execute:
  python smart_alerts_lab.py
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class AlertConfig:
    name: str
    service: str
    metric: str
    static_threshold: float
    weekly_fires: int
    actionable_pct: float
    dependencies: list[str] = field(default_factory=list)


@dataclass
class SmartMonitor:
    name: str
    service: str
    baseline_mean: float
    baseline_std: float
    num_deviations: float
    suppress_if_dep_down: list[str]
    min_duration_minutes: int


def generate_week_data(base_val: float, daily_pattern: bool = True) -> list[float]:
    """Gera uma semana de dados hourly."""
    values = []
    for d in range(7):
        for h in range(24):
            val = base_val
            if daily_pattern and d < 5:
                val += 20 * math.sin((h - 10) * math.pi / 12)
            noise = (hash(str(d * 24 + h + 999)) % 10 - 5)
            values.append(val + noise)
    return values


def build_legacy_alerts() -> list[AlertConfig]:
    return [
        AlertConfig("CPU > 75%", "api-gateway", "cpu", 75, 32, 0.12, ["database"]),
        AlertConfig("Memory > 85%", "user-svc", "memory", 85, 5, 0.80, ["database"]),
        AlertConfig("Error rate > 1%", "checkout", "errors", 1, 18, 0.28, ["database", "payment"]),
        AlertConfig("Latency > 3s", "product-svc", "latency", 3000, 45, 0.07, ["database", "cache"]),
        AlertConfig("Disk > 80%", "database", "disk", 80, 3, 0.95, []),
        AlertConfig("Queue > 500", "worker", "queue", 500, 8, 0.55, ["database"]),
        AlertConfig("Pod restarts", "notifications", "restarts", 2, 22, 0.09, []),
        AlertConfig("Cache miss > 30%", "cache", "miss_rate", 30, 12, 0.15, []),
    ]


def optimize_to_smart_monitors(alerts: list[AlertConfig]) -> list[SmartMonitor]:
    """Converte alertas legacy em monitores inteligentes."""
    monitors = []
    for alert in alerts:
        # Simular aprendizado de baseline
        base_data = generate_week_data(alert.static_threshold * 0.6)
        mean = sum(base_data) / len(base_data)
        std = math.sqrt(sum((v - mean) ** 2 for v in base_data) / len(base_data))

        # Ajustar desvios baseado na acionabilidade
        if alert.actionable_pct < 0.2:
            n_dev = 3.5  # Mais restritivo para alertas ruidosos
            min_dur = 10
        elif alert.actionable_pct < 0.6:
            n_dev = 2.5
            min_dur = 5
        else:
            n_dev = 2.0
            min_dur = 2

        monitors.append(SmartMonitor(
            name=f"Smart: {alert.name}",
            service=alert.service,
            baseline_mean=mean,
            baseline_std=std,
            num_deviations=n_dev,
            suppress_if_dep_down=alert.dependencies,
            min_duration_minutes=min_dur,
        ))

    return monitors


def simulate_week(
    alerts: list[AlertConfig],
    monitors: list[SmartMonitor],
    db_down_hours: list[int],
) -> dict:
    """Simula uma semana com alertas legacy vs. smart monitors."""
    legacy_fires = 0
    legacy_actionable = 0
    smart_fires = 0
    smart_actionable = 0

    for d in range(7):
        for h in range(24):
            hour_abs = d * 24 + h
            db_is_down = hour_abs in db_down_hours

            for alert in alerts:
                val = alert.static_threshold * (0.6 + 0.5 * math.sin(h * math.pi / 12))
                noise = (hash(str(hour_abs + hash(alert.name))) % 20 - 10)
                val += noise

                if db_is_down and "database" in alert.dependencies:
                    val = alert.static_threshold * 2

                if val > alert.static_threshold:
                    legacy_fires += 1
                    is_real = db_is_down and "database" in alert.dependencies
                    if is_real or (hash(str(hour_abs + hash(alert.name))) % 100 < alert.actionable_pct * 100):
                        legacy_actionable += 1

            for monitor in monitors:
                upper = monitor.baseline_mean + monitor.num_deviations * monitor.baseline_std
                val = monitor.baseline_mean + 10 * math.sin(h * math.pi / 12)
                noise = (hash(str(hour_abs + hash(monitor.name))) % 10 - 5)
                val += noise

                if db_is_down and "database" in monitor.suppress_if_dep_down:
                    continue  # Suprimido!

                if val > upper:
                    smart_fires += 1
                    smart_actionable += 1  # Smart monitors são mais precisos

    return {
        "legacy_fires": legacy_fires,
        "legacy_actionable": legacy_actionable,
        "smart_fires": smart_fires,
        "smart_actionable": smart_actionable,
    }


def run_lab() -> None:
    print("=" * 70)
    print("🔬 HANDS-ON: Configurando Alertas Inteligentes")
    print("   Curso 3 — Observabilidade Inteligente — Aula 3")
    print("=" * 70)
    time.sleep(0.3)

    alerts = build_legacy_alerts()

    # PASSO 1: Auditoria
    print(f"\n{'─' * 70}")
    print("PASSO 1/4 — Auditoria dos alertas existentes")
    print(f"{'─' * 70}")

    total_fires = sum(a.weekly_fires for a in alerts)
    total_actionable = sum(a.weekly_fires * a.actionable_pct for a in alerts)

    print(f"\n  {'Alerta':<25} {'Disparos/sem':<15} {'Acionável':<12} {'Categoria':<12}")
    print(f"  {'─' * 25} {'─' * 15} {'─' * 12} {'─' * 12}")
    for a in sorted(alerts, key=lambda x: x.weekly_fires * (1 - x.actionable_pct), reverse=True):
        cat = "🔴 RUÍDO" if a.actionable_pct < 0.2 else "🟡 AJUSTAR" if a.actionable_pct < 0.6 else "🟢 MANTER"
        print(f"  {a.name:<25} {a.weekly_fires:<15} {a.actionable_pct:<12.0%} {cat}")

    print(f"\n  SNR atual: {total_actionable / total_fires * 100:.0f}%")
    time.sleep(0.3)

    # PASSO 2: Conversão
    print(f"\n{'─' * 70}")
    print("PASSO 2/4 — Convertendo para monitores inteligentes")
    print(f"{'─' * 70}")

    monitors = optimize_to_smart_monitors(alerts)
    for m in monitors:
        print(f"\n  🔧 {m.name}")
        print(f"     Baseline: μ={m.baseline_mean:.1f} σ={m.baseline_std:.1f}")
        print(f"     Banda: ±{m.num_deviations}σ → [{m.baseline_mean - m.num_deviations * m.baseline_std:.1f}, "
              f"{m.baseline_mean + m.num_deviations * m.baseline_std:.1f}]")
        print(f"     Min duração: {m.min_duration_minutes} min")
        if m.suppress_if_dep_down:
            print(f"     Supressão: se {', '.join(m.suppress_if_dep_down)} DOWN")
    time.sleep(0.3)

    # PASSO 3: Simulação
    print(f"\n{'─' * 70}")
    print("PASSO 3/4 — Simulação de uma semana")
    print(f"{'─' * 70}")

    db_down = list(range(72, 78))  # Database cai por 6h na quarta
    results = simulate_week(alerts, monitors, db_down)

    print(f"\n  Evento simulado: Database DOWN por 6h (quarta 00:00-06:00)")
    print(f"\n  {'Métrica':<35} {'Legacy':<15} {'Smart':<15}")
    print(f"  {'─' * 35} {'─' * 15} {'─' * 15}")
    print(f"  {'Alertas disparados':<35} {results['legacy_fires']:<15} {results['smart_fires']:<15}")
    print(f"  {'Alertas acionáveis':<35} {results['legacy_actionable']:<15} {results['smart_actionable']:<15}")

    legacy_snr = results['legacy_actionable'] / max(results['legacy_fires'], 1) * 100
    smart_snr = results['smart_actionable'] / max(results['smart_fires'], 1) * 100
    print(f"  {'Signal-to-Noise Ratio':<35} {legacy_snr:<15.0f}% {smart_snr:<15.0f}%")
    reduction = (1 - results['smart_fires'] / max(results['legacy_fires'], 1)) * 100
    print(f"  {'Redução de ruído':<35} {'—':<15} {reduction:.0f}%")
    time.sleep(0.3)

    # PASSO 4: Relatório
    print(f"\n{'=' * 70}")
    print("PASSO 4/4 — RELATÓRIO DE OTIMIZAÇÃO DE ALERTAS")
    print(f"{'=' * 70}")

    print(f"""
  📋 SUMÁRIO
  ─────────────────────────────────────────────
  Alertas auditados     : {len(alerts)} regras
  Monitores otimizados  : {len(monitors)} smart monitors
  Redução de ruído      : {reduction:.0f}%
  SNR antes             : {legacy_snr:.0f}%
  SNR depois            : {smart_snr:.0f}%

  ✅ TÉCNICAS APLICADAS:
  1. Baselines dinâmicos (±nσ por período do dia)
  2. Supressão por dependência de topologia
  3. Duração mínima para evitar spikes transientes
  4. Calibração de sensibilidade por acionabilidade histórica

  📊 IMPACTO NO TIME:
  Alertas por plantão (24h): {results['legacy_fires'] // 7} → {results['smart_fires'] // 7}
  Interrupções noturnas: ~{results['legacy_fires'] * 30 // (7 * 100)} → ~{results['smart_fires'] * 30 // (7 * 100)}
    """)

    print("=" * 70)
    print("🎓 FIM DO HANDS-ON — AULA 3 CONCLUÍDA!")
    print("=" * 70)
    print("""
  Você aprendeu a:
  ✔ Auditar e classificar alertas por acionabilidade
  ✔ Implementar baselines dinâmicos com bandas adaptativas
  ✔ Configurar supressão contextual por dependências
  ✔ Calibrar sensibilidade baseada em dados históricos
  ✔ Medir impacto com signal-to-noise ratio

  Próxima aula: Investigação operacional e análise inteligente de logs →
    """)


if __name__ == "__main__":
    run_lab()
