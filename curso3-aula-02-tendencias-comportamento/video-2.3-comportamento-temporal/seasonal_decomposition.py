"""
Vídeo 2.3 — Analisando comportamento operacional ao longo do tempo
===================================================================
Demonstra decomposição sazonal de séries temporais para diferenciar
picos normais (diários, semanais) de variações anômalas.

Conceitos demonstrados:
- Decomposição de séries temporais: tendência + sazonalidade + resíduo
- Padrões diários e semanais em métricas de infraestrutura
- Detecção de anomalias via componente residual
- Média móvel para extração de tendência
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class DecomposedSeries:
    """Resultado da decomposição de uma série temporal."""
    timestamps: list[datetime]
    observed: list[float]
    trend: list[float]
    seasonal: list[float]
    residual: list[float]


def moving_average(values: list[float], window: int) -> list[float]:
    """Calcula média móvel centrada."""
    result = []
    half = window // 2
    for i in range(len(values)):
        start = max(0, i - half)
        end = min(len(values), i + half + 1)
        result.append(sum(values[start:end]) / (end - start))
    return result


def generate_weekly_traffic() -> tuple[list[datetime], list[float]]:
    """
    Gera dados de tráfego com padrões diários e semanais realistas.
    - Padrão diário: pico às 10h e 15h, vale às 3h
    - Padrão semanal: menor nos fins de semana
    - Tendência crescente leve
    - Uma anomalia plantada no dia 18
    """
    base = datetime(2024, 6, 1)
    timestamps = []
    values = []

    for day in range(28):  # 4 semanas
        date = base + timedelta(days=day)
        weekday = date.weekday()

        # Fator semanal (seg=0 a dom=6)
        weekly_factor = {
            0: 1.0, 1: 1.05, 2: 1.1, 3: 1.05,
            4: 0.95, 5: 0.6, 6: 0.5,
        }[weekday]

        for hour in range(24):
            ts = date.replace(hour=hour)
            timestamps.append(ts)

            # Padrão diário (picos às 10h e 15h)
            hourly = 1000 * (
                0.3 + 0.5 * math.exp(-((hour - 10) ** 2) / 8)
                + 0.4 * math.exp(-((hour - 15) ** 2) / 10)
            )

            # Tendência crescente
            trend_val = day * 8

            # Sazonalidade semanal
            value = (hourly * weekly_factor) + trend_val

            # Ruído
            noise = (hash(str(day * 100 + hour)) % 40 - 20)

            # Anomalia plantada: dia 18, entre 14h e 16h
            anomaly = 0
            if day == 18 and 14 <= hour <= 16:
                anomaly = 800  # Pico anômalo

            values.append(value + noise + anomaly)

    return timestamps, values


def decompose(
    timestamps: list[datetime], values: list[float], period: int = 24
) -> DecomposedSeries:
    """
    Decomposição aditiva simplificada: observed = trend + seasonal + residual.
    """
    # 1. Extrair tendência com média móvel
    trend = moving_average(values, window=period)

    # 2. Extrair sazonalidade (média por posição no período)
    detrended = [v - t for v, t in zip(values, trend)]
    seasonal_avg: dict[int, list[float]] = {}
    for i, val in enumerate(detrended):
        pos = i % period
        seasonal_avg.setdefault(pos, []).append(val)

    seasonal_profile = {pos: sum(vals) / len(vals) for pos, vals in seasonal_avg.items()}

    seasonal = [seasonal_profile[i % period] for i in range(len(values))]

    # 3. Resíduo = observado - tendência - sazonalidade
    residual = [v - t - s for v, t, s in zip(values, trend, seasonal)]

    return DecomposedSeries(
        timestamps=timestamps,
        observed=values,
        trend=trend,
        seasonal=seasonal,
        residual=residual,
    )


def sparkline(values: list[float], width: int = 60) -> str:
    """Sparkline ASCII."""
    chars = "▁▂▃▄▅▆▇█"
    step = max(1, len(values) // width)
    sampled = [values[i] for i in range(0, len(values), step)][:width]
    mn, mx = min(sampled), max(sampled)
    rng = mx - mn if mx != mn else 1
    return "".join(chars[int((v - mn) / rng * (len(chars) - 1))] for v in sampled)


def detect_anomalies(decomposed: DecomposedSeries, threshold: float = 2.5) -> list[int]:
    """Detecta anomalias via resíduo: |resíduo| > threshold * std."""
    residuals = decomposed.residual
    mean_r = sum(residuals) / len(residuals)
    std_r = math.sqrt(sum((r - mean_r) ** 2 for r in residuals) / len(residuals))

    anomalies = []
    for i, r in enumerate(residuals):
        if abs(r - mean_r) > threshold * std_r:
            anomalies.append(i)

    return anomalies


def run_demo() -> None:
    print("=" * 70)
    print("🕐 Demo: Decomposição Sazonal de Séries Temporais")
    print("   Curso 3 — Observabilidade Inteligente")
    print("=" * 70)

    timestamps, values = generate_weekly_traffic()
    decomposed = decompose(timestamps, values, period=24)

    # Série original
    print(f"\n{'─' * 70}")
    print("📊 SÉRIE ORIGINAL (requests/hora — 4 semanas)")
    print(f"{'─' * 70}")
    print(f"\n  {sparkline(decomposed.observed)}")
    print(f"  Min: {min(decomposed.observed):.0f}  Max: {max(decomposed.observed):.0f}")

    # Tendência
    print(f"\n{'─' * 70}")
    print("📈 COMPONENTE: TENDÊNCIA (média móvel 24h)")
    print(f"{'─' * 70}")
    print(f"\n  {sparkline(decomposed.trend)}")
    print(f"  → Crescimento gradual ao longo das 4 semanas")

    # Sazonalidade
    print(f"\n{'─' * 70}")
    print("🔄 COMPONENTE: SAZONALIDADE (padrão diário)")
    print(f"{'─' * 70}")
    daily = decomposed.seasonal[:24]
    print(f"\n  Perfil de 24 horas:")
    for h in range(24):
        bar_len = max(0, int((daily[h] + 400) / 30))
        print(f"    {h:02d}h {'█' * bar_len} {daily[h]:+.0f}")
    print(f"  → Picos às 10h e 15h, vale entre 1h-5h")

    # Padrão semanal
    print(f"\n{'─' * 70}")
    print("📅 PADRÃO SEMANAL (tráfego médio por dia)")
    print(f"{'─' * 70}")
    for w in range(4):
        print(f"\n  Semana {w + 1}:")
        for d in range(7):
            day_idx = w * 7 + d
            day_start = day_idx * 24
            day_end = day_start + 24
            if day_end <= len(decomposed.observed):
                day_avg = sum(decomposed.observed[day_start:day_end]) / 24
                day_name = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"][d]
                bar = "█" * int(day_avg / 30)
                print(f"    {day_name}: {bar} {day_avg:.0f} req/h")

    # Resíduos e anomalias
    print(f"\n{'─' * 70}")
    print("🔍 COMPONENTE: RESÍDUO (desvios da normalidade)")
    print(f"{'─' * 70}")
    print(f"\n  {sparkline(decomposed.residual)}")

    anomalies = detect_anomalies(decomposed)
    if anomalies:
        print(f"\n  ⚠️  {len(anomalies)} anomalias detectadas (|resíduo| > 2.5σ):")
        for idx in anomalies[:10]:
            ts = decomposed.timestamps[idx]
            res = decomposed.residual[idx]
            obs = decomposed.observed[idx]
            print(f"    [{ts.strftime('%d/%m %H:%M')}] observado={obs:.0f} "
                  f"resíduo={res:+.0f}")
    else:
        print(f"\n  ✅ Nenhuma anomalia detectada")

    # Interpretação
    print("\n" + "=" * 70)
    print("📌 INTERPRETAÇÃO")
    print("=" * 70)
    print("""
  A decomposição sazonal revela:

  1. TENDÊNCIA: Crescimento estável de ~8 req/h/dia (planejamento)
  2. SAZONALIDADE DIÁRIA: Picos previsíveis às 10h e 15h (esperado)
  3. SAZONALIDADE SEMANAL: Fins de semana com 40-50% menos tráfego
  4. ANOMALIA: Pico incomum no dia 19/06 entre 14h-16h
     → Este pico NÃO é explicado pela sazonalidade, exige investigação

  Sem decomposição, o pico do dia 19 poderia ser confundido com
  um pico sazonal normal. O componente residual isola exatamente
  o que é "anormal" vs. o que é comportamento esperado.

  Na Aula 2.4, veremos como detectar changepoints — mudanças
  sutis de comportamento que passam despercebidas por alertas comuns.
    """)


if __name__ == "__main__":
    run_demo()
