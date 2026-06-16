"""
Vídeo 2.3 — Análise operacional de métricas e séries temporais
==============================================================
Demonstra como interpretar a evolução temporal de métricas
e prever tendências de esgotamento antes que causem incidentes.

Conceitos demonstrados:
- Regressão linear simples para previsão de tendência
- Cálculo de TTL (Time-To-Limit): quando o recurso vai se esgotar
- Análise de sazonalidade semanal
- Forecast básico de métricas de capacidade
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean


# ---------------------------------------------------------------------------
# Gerador de série de uso de disco (crescimento gradual + sazonalidade)
# ---------------------------------------------------------------------------

def generate_disk_usage_series(
    days: int = 30,
    initial_pct: float = 45.0,
    growth_per_day: float = 1.2,  # % por dia
) -> list[tuple[datetime, float]]:
    """
    Gera uma série de uso de disco com crescimento linear
    e variação diária (mais escrita durante horário comercial).
    """
    series = []
    base = datetime(2024, 5, 1, 0, 0, 0)

    for hour in range(days * 24):
        ts = base + timedelta(hours=hour)
        day = hour // 24
        h = ts.hour

        # Crescimento linear base
        base_usage = initial_pct + day * growth_per_day

        # Variação diária (pico durante horário comercial)
        daily_var = 0.5 * math.sin(math.pi * max(0, h - 6) / 12) if 6 <= h <= 18 else 0

        noise = random.gauss(0, 0.3)
        usage = max(0.0, min(100.0, base_usage + daily_var + noise))
        series.append((ts, round(usage, 2)))

    return series


# ---------------------------------------------------------------------------
# Análise de tendência e previsão
# ---------------------------------------------------------------------------

@dataclass
class TrendForecast:
    metric_name: str
    current_value: float
    slope_per_day: float          # taxa de crescimento diária
    r_squared: float              # qualidade do ajuste (0-1)
    days_to_threshold: float      # tempo até atingir o limite crítico
    forecast_30d: float           # valor previsto em 30 dias
    forecast_60d: float           # valor previsto em 60 dias
    threshold: float              # limite crítico configurado
    severity: str                 # NORMAL | WARNING | CRITICAL


def linear_regression(x: list[float], y: list[float]) -> tuple[float, float, float]:
    """
    Regressão linear simples. Retorna (slope, intercept, r_squared).
    """
    n = len(x)
    if n < 2:
        return 0.0, y[0] if y else 0.0, 0.0

    x_mean = mean(x)
    y_mean = mean(y)

    numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
    denominator = sum((xi - x_mean) ** 2 for xi in x)

    if denominator == 0:
        return 0.0, y_mean, 0.0

    slope = numerator / denominator
    intercept = y_mean - slope * x_mean

    # R² (coeficiente de determinação)
    ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, y))
    ss_tot = sum((yi - y_mean) ** 2 for yi in y)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    return slope, intercept, r_squared


def forecast_metric(
    series: list[tuple[datetime, float]],
    metric_name: str = "disk_usage_pct",
    threshold: float = 85.0,
) -> TrendForecast:
    """
    Analisa a tendência da série e calcula quando o threshold será atingido.
    """
    # Converte timestamps para índice numérico (dias desde o início)
    base_ts = series[0][0]
    x = [(ts - base_ts).total_seconds() / 86400 for ts, _ in series]
    y = [val for _, val in series]

    slope, intercept, r_squared = linear_regression(x, y)

    current = y[-1]
    current_day = x[-1]

    # Previsões
    forecast_30d = slope * (current_day + 30) + intercept
    forecast_60d = slope * (current_day + 60) + intercept

    # Tempo até atingir o threshold
    if slope > 0 and current < threshold:
        days_to_threshold = (threshold - (slope * current_day + intercept)) / slope
    elif current >= threshold:
        days_to_threshold = 0.0
    else:
        days_to_threshold = float("inf")

    # Severidade
    if days_to_threshold <= 7:
        severity = "🔴 CRÍTICO"
    elif days_to_threshold <= 30:
        severity = "🟡 ATENÇÃO"
    else:
        severity = "🟢 NORMAL"

    return TrendForecast(
        metric_name=metric_name,
        current_value=round(current, 1),
        slope_per_day=round(slope, 4),           # slope já está em %/dia (x em dias)
        r_squared=round(r_squared, 3),
        days_to_threshold=round(days_to_threshold, 1),
        forecast_30d=round(forecast_30d, 1),
        forecast_60d=round(forecast_60d, 1),
        threshold=threshold,
        severity=severity,
    )


def print_forecast_report(forecast: TrendForecast) -> None:
    print("\n" + "=" * 65)
    print(f"📈 ANÁLISE DE TENDÊNCIA — {forecast.metric_name}")
    print("=" * 65)
    print(f"""
  Valor atual          : {forecast.current_value}%
  Crescimento diário   : +{forecast.slope_per_day:.2f}% / dia
  Qualidade do modelo  : R² = {forecast.r_squared:.3f} ({'bom' if forecast.r_squared > 0.8 else 'médio'})

  Limite crítico       : {forecast.threshold}%
  Atingido em          : {forecast.days_to_threshold:.0f} dias
  Severidade           : {forecast.severity}

  Previsão +30 dias    : {forecast.forecast_30d}%
  Previsão +60 dias    : {forecast.forecast_60d}%
    """)

    if forecast.days_to_threshold != float("inf"):
        alert_date = datetime.now() + timedelta(days=forecast.days_to_threshold)
        print(f"  ⚠️  Ação necessária antes de: {alert_date.strftime('%d/%m/%Y')}")
        print(f"     Recomendação: provisionar capacidade adicional ou arquivar dados.")


if __name__ == "__main__":
    print("🔬 Demo: Análise Operacional de Métricas e Séries Temporais")
    print("     Nível 1 — AIOps & Automação de Incidentes\n")

    print("  Gerando 30 dias de histórico de uso de disco...")
    series = generate_disk_usage_series(days=30, initial_pct=45.0, growth_per_day=1.3)

    forecast = forecast_metric(series, metric_name="disk_usage_pct", threshold=85.0)
    print_forecast_report(forecast)

    # Visualização da série (amostra diária)
    print("  Evolução diária (1 ponto por dia):")
    for ts, val in series[::24]:
        bar = "█" * int(val / 2)
        print(f"  {ts.strftime('%d/%m')} [{bar:<43}] {val:5.1f}%")
