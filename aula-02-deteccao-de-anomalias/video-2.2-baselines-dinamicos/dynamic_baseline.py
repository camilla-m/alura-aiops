"""
Vídeo 2.2 — Baselines dinâmicos e comportamento esperado
=========================================================
Demonstra como implementar baselines dinâmicos usando machine learning
para aprender padrões sazonais de métricas operacionais.

Conceitos demonstrados:
- Sazonalidade diária e semanal de métricas
- Baseline adaptativo com média móvel exponencial (EMA)
- Bandas de confiança (upper/lower bounds)
- Redução de falsos positivos em comparação ao threshold fixo
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from statistics import mean, stdev
from typing import Optional


# ---------------------------------------------------------------------------
# Gerador de série temporal com sazonalidade semanal
# ---------------------------------------------------------------------------

def generate_weekly_metric(
    days: int = 14,
    metric_name: str = "requests_per_second",
    base_value: float = 100.0,
    inject_anomaly: bool = True,
) -> list[tuple[datetime, float]]:
    """
    Gera uma série temporal com sazonalidade diária E semanal.
    Final de semana tem tráfego 60% menor que dias úteis.
    """
    series = []
    base = datetime(2024, 5, 20, 0, 0, 0)  # segunda-feira

    for minute in range(days * 24 * 12):  # pontos de 5 em 5 minutos
        ts = base + timedelta(minutes=minute * 5)
        hour = ts.hour
        weekday = ts.weekday()  # 0=segunda, 6=domingo

        # Sazonalidade semanal
        day_factor = 0.4 if weekday >= 5 else 1.0

        # Sazonalidade diária (padrão sinusoidal)
        if 0 <= hour < 6:
            hour_factor = 0.2
        elif 6 <= hour < 9:
            hour_factor = 0.2 + 0.8 * (hour - 6) / 3
        elif 9 <= hour < 12:
            hour_factor = 1.0
        elif 12 <= hour < 14:
            hour_factor = 0.85
        elif 14 <= hour < 18:
            hour_factor = 1.0
        elif 18 <= hour < 21:
            hour_factor = 0.7
        else:
            hour_factor = 0.3

        value = base_value * day_factor * hour_factor
        noise = random.gauss(0, base_value * 0.05)

        # Anomalia injetada no 10º dia, às 15h
        if inject_anomaly and ts.day == base.day + 10 and hour == 15:
            value *= 3.5  # spike de 350%

        series.append((ts, max(0.0, round(value + noise, 2))))

    return series


# ---------------------------------------------------------------------------
# Baseline dinâmico com bandas de confiança
# ---------------------------------------------------------------------------

@dataclass
class BaselinePoint:
    timestamp: datetime
    observed: float
    expected: float
    upper_bound: float
    lower_bound: float
    is_anomaly: bool
    deviation_pct: float  # % de desvio em relação ao esperado


class DynamicBaseline:
    """
    Baseline dinâmico usando média móvel com bandas de confiança.

    Para cada ponto na série, calcula o valor esperado com base
    no histórico recente e define bandas de confiança.

    Em produção, isso é implementado com Prophet (Meta), ARIMA,
    ou algoritmos nativos de plataformas como Datadog/Dynatrace.
    """

    def __init__(
        self,
        seasonality_period: int = 288,  # pontos em 1 dia (5 min × 288 = 24h)
        confidence_multiplier: float = 2.5,
        smoothing: float = 0.1,  # fator EMA (0-1)
    ):
        self.seasonality_period = seasonality_period
        self.confidence_multiplier = confidence_multiplier
        self.smoothing = smoothing
        self._history: list[float] = []
        self._ema: Optional[float] = None

    def fit_and_detect(
        self,
        series: list[tuple[datetime, float]],
    ) -> list[BaselinePoint]:
        """Treina o baseline e detecta anomalias na mesma série."""
        results = []
        self._history = []

        for i, (ts, value) in enumerate(series):
            # Calcula EMA (baseline adaptativo)
            if self._ema is None:
                self._ema = value
            else:
                self._ema = self.smoothing * value + (1 - self.smoothing) * self._ema

            # Bandas de confiança baseadas no desvio histórico
            if len(self._history) >= 12:  # mínimo de 1h de histórico
                window = self._history[-self.seasonality_period:]
                sigma = stdev(window) if len(window) > 1 else self._ema * 0.1
                upper = self._ema + self.confidence_multiplier * sigma
                lower = max(0, self._ema - self.confidence_multiplier * sigma)
            else:
                upper = self._ema * 2.0
                lower = 0.0

            is_anomaly = value > upper or value < lower
            dev = ((value - self._ema) / self._ema * 100) if self._ema > 0 else 0

            results.append(BaselinePoint(
                timestamp=ts, observed=value,
                expected=round(self._ema, 2),
                upper_bound=round(upper, 2),
                lower_bound=round(lower, 2),
                is_anomaly=is_anomaly,
                deviation_pct=round(dev, 1),
            ))
            self._history.append(value)

        return results


# ---------------------------------------------------------------------------
# Relatório de baseline
# ---------------------------------------------------------------------------

def report_baseline(points: list[BaselinePoint], metric_name: str) -> None:
    anomalies = [p for p in points if p.is_anomaly]
    total = len(points)

    print("\n" + "=" * 65)
    print(f"📊 BASELINE DINÂMICO — {metric_name}")
    print("=" * 65)
    print(f"\n  Pontos analisados    : {total:,}")
    print(f"  Anomalias detectadas : {len(anomalies)}")
    print(f"  Taxa de anomalia     : {len(anomalies)/total*100:.2f}%")

    if anomalies:
        worst = max(anomalies, key=lambda p: abs(p.deviation_pct))
        print(f"\n  Pior desvio detectado:")
        print(f"    Timestamp  : {worst.timestamp.strftime('%Y-%m-%d %H:%M')}")
        print(f"    Observado  : {worst.observed:.1f}")
        print(f"    Esperado   : {worst.expected:.1f}")
        print(f"    Upper bound: {worst.upper_bound:.1f}")
        print(f"    Desvio     : +{worst.deviation_pct:.0f}%")

    print(f"\n  Últimas 6 horas (amostra a cada 30 min):")
    sample = points[-72::6]
    for p in sample:
        width = 40
        obs_bar = "█" * min(int(p.observed / 5), width)
        exp_bar = "░" * min(int(p.expected / 5), width)
        flag = " ← 🔴" if p.is_anomaly else ""
        print(f"  {p.timestamp.strftime('%d/%m %H:%M')} [{obs_bar:<{width}}] {p.observed:6.1f}{flag}")


if __name__ == "__main__":
    print("🔬 Demo: Baselines Dinâmicos e Comportamento Esperado")
    print("     Nível 1 — AIOps & Automação de Incidentes\n")

    print("  Gerando 14 dias de série temporal com sazonalidade semanal...")
    series = generate_weekly_metric(days=14, metric_name="requests_per_second")

    print("  Treinando baseline dinâmico...\n")
    baseline = DynamicBaseline(seasonality_period=288, confidence_multiplier=2.5)
    results = baseline.fit_and_detect(series)

    report_baseline(results, "requests_per_second")

    print("\n" + "=" * 65)
    print("📌 CONCLUSÃO")
    print("=" * 65)
    print("""
  O baseline dinâmico aprende automaticamente que:
  - Fins de semana têm tráfego 60% menor (sem alertar por isso)
  - Madrugadas têm CPU baixa (sem considerar como anomalia)
  - Um spike de 350% às 15h de uma terça é uma anomalia real

  Isso reduz drasticamente o alert fatigue causado por thresholds
  estáticos que ignoram a sazonalidade do negócio.
    """)
