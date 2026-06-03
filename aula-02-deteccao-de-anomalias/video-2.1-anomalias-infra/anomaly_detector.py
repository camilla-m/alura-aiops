"""
Vídeo 2.1 — Detectando comportamento anormal em infraestrutura
==============================================================
Demonstra como identificar anomalias em métricas de hardware
(CPU, memória) e de rede (latência, tráfego) através da análise
de desvios em relação ao comportamento esperado.

Conceitos demonstrados:
- Diferença entre pico esperado vs. anomalia real
- Detecção por threshold estático (limite fixo)
- Detecção por Z-score (desvio padrão)
- Visualização comparativa dos dois métodos
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean, stdev
from typing import Optional


# ---------------------------------------------------------------------------
# Gerador de séries temporais realistas
# ---------------------------------------------------------------------------

def generate_cpu_series(
    hours: int = 24,
    resolution_minutes: int = 5,
    inject_anomaly_at: Optional[int] = None,  # hora (0-23) para injetar anomalia
) -> list[tuple[datetime, float]]:
    """
    Gera uma série temporal de CPU com padrão diário realista.

    Padrão:
    - Madrugada (0-6h): 15-25% CPU
    - Horário comercial (8-18h): 45-65% CPU
    - Pico de meio-dia (12h): até 75%
    - Anomalia injetada: spike de 95-100%
    """
    series = []
    base = datetime(2024, 6, 3, 0, 0, 0)
    steps = (hours * 60) // resolution_minutes

    for i in range(steps):
        ts = base + timedelta(minutes=i * resolution_minutes)
        hour = ts.hour

        # Padrão sinusoidal diário
        if 0 <= hour < 6:
            base_cpu = 20.0
        elif 6 <= hour < 8:
            base_cpu = 30.0 + (hour - 6) * 5
        elif 8 <= hour < 18:
            # Pico ao meio-dia
            base_cpu = 50.0 + 15.0 * math.sin(math.pi * (hour - 8) / 10)
        elif 18 <= hour < 22:
            base_cpu = 40.0 - (hour - 18) * 3
        else:
            base_cpu = 20.0

        noise = random.gauss(0, 3)  # ruído gaussiano

        # Injeta anomalia
        if inject_anomaly_at and hour == inject_anomaly_at:
            if i % (60 // resolution_minutes) < 3:  # dura ~15 min
                base_cpu = 97.0 + random.uniform(0, 3)

        cpu = max(0.0, min(100.0, base_cpu + noise))
        series.append((ts, round(cpu, 2)))

    return series


# ---------------------------------------------------------------------------
# Detectores de anomalia
# ---------------------------------------------------------------------------

@dataclass
class AnomalyDetection:
    timestamp: datetime
    value: float
    is_anomaly: bool
    method: str
    threshold: float
    score: float  # distância do limite (quanto mais alto, mais anômalo)


def detect_by_static_threshold(
    series: list[tuple[datetime, float]],
    threshold: float = 85.0,
) -> list[AnomalyDetection]:
    """
    Método clássico: threshold fixo.
    Simples, mas gera muitos falsos positivos e negativos.
    """
    results = []
    for ts, value in series:
        is_anomaly = value > threshold
        results.append(AnomalyDetection(
            timestamp=ts, value=value,
            is_anomaly=is_anomaly, method="static_threshold",
            threshold=threshold,
            score=max(0, value - threshold),
        ))
    return results


def detect_by_zscore(
    series: list[tuple[datetime, float]],
    window_size: int = 24,   # número de pontos na janela
    z_threshold: float = 2.5,
) -> list[AnomalyDetection]:
    """
    Método estatístico: Z-score com janela deslizante.
    Detecta desvios relativos ao comportamento recente.
    Muito mais preciso que threshold estático.
    """
    values = [v for _, v in series]
    results = []

    for i, (ts, value) in enumerate(series):
        if i < window_size:
            # Janela insuficiente — usa o que tem
            window = values[:i+1]
        else:
            window = values[i - window_size:i]

        if len(window) < 2:
            results.append(AnomalyDetection(ts, value, False, "zscore", 0, 0))
            continue

        mu = mean(window)
        sigma = stdev(window)
        z = abs(value - mu) / sigma if sigma > 0 else 0

        results.append(AnomalyDetection(
            timestamp=ts, value=value,
            is_anomaly=z > z_threshold, method="zscore",
            threshold=mu + z_threshold * sigma,
            score=z,
        ))
    return results


# ---------------------------------------------------------------------------
# Relatório comparativo
# ---------------------------------------------------------------------------

def compare_methods(series: list[tuple[datetime, float]]) -> None:
    static_results = detect_by_static_threshold(series)
    zscore_results = detect_by_zscore(series)

    static_anomalies = [r for r in static_results if r.is_anomaly]
    zscore_anomalies = [r for r in zscore_results if r.is_anomaly]

    print("\n" + "=" * 65)
    print("📊 COMPARAÇÃO: Threshold Estático vs. Z-Score")
    print("=" * 65)
    print(f"\n  Total de pontos analisados: {len(series)}")

    print(f"\n  {'─'*55}")
    print(f"  MÉTODO 1 — Threshold Estático (>85%)")
    print(f"  {'─'*55}")
    print(f"  Anomalias detectadas: {len(static_anomalies)}")
    if static_anomalies:
        max_a = max(static_anomalies, key=lambda x: x.score)
        print(f"  Pico máximo detectado: {max_a.value:.1f}% às {max_a.timestamp.strftime('%H:%M')}")
    print(f"  ⚠️  Problema: horários de pico legítimos podem ultrapassar 85%")
    print(f"     gerando FALSOS POSITIVOS durante o horário comercial.")

    print(f"\n  {'─'*55}")
    print(f"  MÉTODO 2 — Z-Score (desvio padrão, janela deslizante)")
    print(f"  {'─'*55}")
    print(f"  Anomalias detectadas: {len(zscore_anomalies)}")
    if zscore_anomalies:
        max_z = max(zscore_anomalies, key=lambda x: x.score)
        print(f"  Ponto mais anômalo: {max_z.value:.1f}% às {max_z.timestamp.strftime('%H:%M')} (z={max_z.score:.2f})")
    print(f"  ✅ Vantagem: detecta desvios relativos ao comportamento ESPERADO")
    print(f"     para cada hora do dia, reduzindo falsos positivos.")

    # Mini gráfico ASCII
    print(f"\n  {'─'*55}")
    print(f"  VISUALIZAÇÃO — Série Temporal (amostra de 6h)")
    print(f"  {'─'*55}")
    sample = series[::6][:30]  # 1 ponto a cada 30 min, 15h
    for ts, val in sample:
        bar_len = int(val / 3)
        bar = "█" * bar_len
        flag = " ← 🔴 ANOMALIA" if val > 90 else ""
        print(f"  {ts.strftime('%H:%M')} [{bar:<33}] {val:5.1f}%{flag}")


if __name__ == "__main__":
    print("🔬 Demo: Detectando Comportamento Anormal em Infraestrutura")
    print("     Nível 1 — AIOps & Automação de Incidentes\n")

    print("  Gerando série temporal de CPU (24h) com anomalia às 14h...")
    series = generate_cpu_series(hours=24, inject_anomaly_at=14)
    compare_methods(series)

    print("\n" + "=" * 65)
    print("📌 CONCLUSÃO")
    print("=" * 65)
    print("""
  Threshold estático é simples, mas ignora a sazonalidade.
  Z-Score adapta-se ao contexto temporal e reduz falsos positivos.

  No próximo vídeo veremos baselines DINÂMICOS com ML,
  que aprendem sazonalidade semanal automaticamente.
    """)
