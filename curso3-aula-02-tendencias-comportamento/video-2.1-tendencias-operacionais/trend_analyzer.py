"""
Vídeo 2.1 — Identificando tendências em ambientes operacionais
===============================================================
Demonstra como analisar taxas de crescimento contínuo de consumo
em infraestrutura (storage, memória, conexões) usando modelagem
matemática básica para identificar tendências invisíveis.

Conceitos demonstrados:
- Crescimento linear vs. exponencial de recursos
- Regressão linear simples para modelar tendências
- Taxas de crescimento e projeção temporal
- Detecção de desvios crônicos de desempenho
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class MetricSample:
    """Amostra de métrica com timestamp."""
    timestamp: datetime
    value: float
    unit: str


@dataclass
class TrendAnalysis:
    """Resultado da análise de tendência."""
    metric_name: str
    slope_per_day: float
    intercept: float
    current_value: float
    capacity: float
    days_to_exhaustion: Optional[float]
    growth_type: str  # "linear", "exponential", "stable"
    r_squared: float

    def __str__(self) -> str:
        if self.days_to_exhaustion and self.days_to_exhaustion > 0:
            exhaustion = f"{self.days_to_exhaustion:.0f} dias"
        else:
            exhaustion = "N/A (sem tendência de esgotamento)"
        return (
            f"  {self.metric_name}\n"
            f"    Valor atual        : {self.current_value:.1f}\n"
            f"    Capacidade máxima  : {self.capacity:.1f}\n"
            f"    Taxa de crescimento: {self.slope_per_day:.2f}/dia ({self.growth_type})\n"
            f"    R² (confiança)     : {self.r_squared:.3f}\n"
            f"    Esgotamento em     : {exhaustion}\n"
        )


def linear_regression(x: list[float], y: list[float]) -> tuple[float, float, float]:
    """
    Regressão linear simples: y = slope * x + intercept.
    Retorna (slope, intercept, r_squared).
    """
    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi ** 2 for xi in x)
    sum_y2 = sum(yi ** 2 for yi in y)

    denom = n * sum_x2 - sum_x ** 2
    if denom == 0:
        return 0.0, sum_y / n if n > 0 else 0.0, 0.0

    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n

    # R-squared
    ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, y))
    mean_y = sum_y / n
    ss_tot = sum((yi - mean_y) ** 2 for yi in y)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    return slope, intercept, r_squared


def generate_disk_usage_data() -> list[MetricSample]:
    """Simula uso de disco crescendo linearmente ao longo de 90 dias."""
    base = datetime(2024, 4, 1)
    samples = []
    for day in range(90):
        # Crescimento linear: ~2.1 GB/dia + ruído
        value = 420 + day * 2.1 + (hash(str(day)) % 10 - 5) * 0.5
        samples.append(MetricSample(
            timestamp=base + timedelta(days=day),
            value=value,
            unit="GB",
        ))
    return samples


def generate_memory_usage_data() -> list[MetricSample]:
    """Simula memory leak — crescimento lento mas constante."""
    base = datetime(2024, 4, 1)
    samples = []
    for day in range(90):
        # Memory leak: ~0.8% por dia
        base_usage = 45.0  # %
        leak = day * 0.8
        noise = (hash(str(day + 100)) % 10 - 5) * 0.3
        value = min(base_usage + leak + noise, 100.0)
        samples.append(MetricSample(
            timestamp=base + timedelta(days=day),
            value=value,
            unit="%",
        ))
    return samples


def generate_connections_data() -> list[MetricSample]:
    """Simula conexões de banco — estável sem tendência clara."""
    base = datetime(2024, 4, 1)
    samples = []
    for day in range(90):
        # Estável em torno de 45, sem tendência
        value = 45 + (hash(str(day + 200)) % 20 - 10) * 0.5
        samples.append(MetricSample(
            timestamp=base + timedelta(days=day),
            value=value,
            unit="connections",
        ))
    return samples


def analyze_trend(
    metric_name: str,
    samples: list[MetricSample],
    capacity: float,
) -> TrendAnalysis:
    """Analisa a tendência de uma série temporal de métricas."""
    # Converter para dias relativos (eixo X)
    base_ts = samples[0].timestamp
    x = [(s.timestamp - base_ts).total_seconds() / 86400 for s in samples]
    y = [s.value for s in samples]

    slope, intercept, r_squared = linear_regression(x, y)

    # Determinar tipo de crescimento
    if abs(slope) < 0.01:
        growth_type = "estável"
    elif slope > 0:
        growth_type = "linear crescente"
    else:
        growth_type = "linear decrescente"

    # Calcular dias até esgotamento
    current = y[-1]
    if slope > 0 and current < capacity:
        days_to_exhaustion = (capacity - current) / slope
    else:
        days_to_exhaustion = None

    return TrendAnalysis(
        metric_name=metric_name,
        slope_per_day=slope,
        intercept=intercept,
        current_value=current,
        capacity=capacity,
        days_to_exhaustion=days_to_exhaustion,
        growth_type=growth_type,
        r_squared=r_squared,
    )


def print_sparkline(values: list[float], width: int = 50) -> str:
    """Gera um sparkline ASCII para visualização rápida."""
    chars = "▁▂▃▄▅▆▇█"
    min_v = min(values)
    max_v = max(values)
    rng = max_v - min_v if max_v != min_v else 1

    # Amostrar para caber na largura
    step = max(1, len(values) // width)
    sampled = [values[i] for i in range(0, len(values), step)]

    line = ""
    for v in sampled[:width]:
        idx = int((v - min_v) / rng * (len(chars) - 1))
        line += chars[idx]

    return line


def run_demo() -> None:
    print("=" * 70)
    print("📈 Demo: Identificando Tendências em Ambientes Operacionais")
    print("   Curso 3 — Observabilidade Inteligente")
    print("=" * 70)

    scenarios = [
        ("Disco (storage-pool-01)", generate_disk_usage_data(), 1000.0),
        ("Memória (user-service)", generate_memory_usage_data(), 100.0),
        ("Conexões DB (postgres-primary)", generate_connections_data(), 100.0),
    ]

    results: list[TrendAnalysis] = []

    for name, samples, capacity in scenarios:
        print(f"\n{'─' * 70}")
        print(f"📊 MÉTRICA: {name}")
        print(f"{'─' * 70}")

        values = [s.value for s in samples]
        sparkline = print_sparkline(values)
        print(f"\n  Últimos 90 dias: {sparkline}")
        print(f"  Min: {min(values):.1f}  Max: {max(values):.1f}  Atual: {values[-1]:.1f}")

        analysis = analyze_trend(name, samples, capacity)
        results.append(analysis)
        print(f"\n{analysis}")

        # Visualização da projeção
        if analysis.days_to_exhaustion and analysis.days_to_exhaustion > 0:
            bar_current = int(analysis.current_value / analysis.capacity * 40)
            bar_full = 40
            print(f"  Projeção visual:")
            print(f"    [{'█' * bar_current}{'░' * (bar_full - bar_current)}] "
                  f"{analysis.current_value:.0f}/{analysis.capacity:.0f} "
                  f"({analysis.current_value / analysis.capacity * 100:.0f}%)")
            print(f"    ⚠️  Esgotamento estimado em {analysis.days_to_exhaustion:.0f} dias")

    # Resumo com priorização
    print("\n" + "=" * 70)
    print("📋 RESUMO: PRIORIZAÇÃO DE RISCOS OPERACIONAIS")
    print("=" * 70)

    critical = [r for r in results if r.days_to_exhaustion and r.days_to_exhaustion < 30]
    warning = [r for r in results if r.days_to_exhaustion and 30 <= r.days_to_exhaustion < 90]
    stable = [r for r in results if not r.days_to_exhaustion or r.days_to_exhaustion >= 90]

    if critical:
        print("\n  🔴 CRÍTICO (esgotamento < 30 dias):")
        for r in critical:
            print(f"    - {r.metric_name}: {r.days_to_exhaustion:.0f} dias restantes")

    if warning:
        print("\n  🟡 ATENÇÃO (esgotamento < 90 dias):")
        for r in warning:
            print(f"    - {r.metric_name}: {r.days_to_exhaustion:.0f} dias restantes")

    if stable:
        print("\n  🟢 ESTÁVEL (sem risco imediato):")
        for r in stable:
            print(f"    - {r.metric_name}: sem tendência de esgotamento")

    print("\n" + "=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  A análise de tendências transforma dados históricos em alertas
  proativos. Ao invés de esperar o disco lotar às 3h da manhã,
  podemos prever com semanas de antecedência e agir preventivamente.

  Na Aula 2.2, vamos aprofundar a previsão de saturação com
  modelos de regressão aplicados a cenários reais de produção.
    """)


if __name__ == "__main__":
    run_demo()
