"""
Vídeo 2.4 — Detectando desvios em métricas operacionais
========================================================
Demonstra detecção de changepoints — mudanças sutis de
comportamento que passam despercebidas por alertas estáticos.

Conceitos demonstrados:
- Changepoint detection via CUSUM (Cumulative Sum)
- Desvios sutis de latência que thresholds fixos ignoram
- Janela deslizante para detecção de shifts no baseline
- Análise antes/depois de um changepoint
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Changepoint:
    """Um changepoint detectado na série temporal."""
    index: int
    timestamp: datetime
    metric: str
    mean_before: float
    mean_after: float
    shift_magnitude: float
    shift_pct: float
    confidence: float


def generate_latency_with_shift() -> tuple[list[datetime], list[float]]:
    """
    Gera latência com uma mudança sutil que um threshold estático não pega.
    Antes: ~120ms (±15ms)
    Depois: ~165ms (±18ms) — aumento de 37%, mas ainda abaixo do threshold de 500ms
    """
    base = datetime(2024, 7, 1)
    timestamps = []
    values = []
    shift_day = 45  # Changepoint no dia 45

    for day in range(90):
        for hour in [0, 6, 12, 18]:  # 4 amostras por dia
            ts = base + timedelta(days=day, hours=hour)
            timestamps.append(ts)

            idx = day * 4 + hour // 6
            noise = (hash(str(idx)) % 30 - 15)

            if day < shift_day:
                value = 120 + noise
            else:
                value = 165 + noise * 1.2  # Shift + mais variância

            values.append(max(value, 10))

    return timestamps, values


def generate_error_rate_with_gradual_drift() -> tuple[list[datetime], list[float]]:
    """
    Gera error rate com drift gradual — crescimento lento que
    eventualmente ultrapassa o threshold.
    """
    base = datetime(2024, 7, 1)
    timestamps = []
    values = []

    for day in range(90):
        for hour in [0, 8, 16]:
            ts = base + timedelta(days=day, hours=hour)
            timestamps.append(ts)

            idx = day * 3 + hour // 8
            noise = (hash(str(idx + 5000)) % 10 - 5) * 0.001

            # Drift gradual a partir do dia 30
            if day < 30:
                value = 0.005 + noise
            else:
                drift = (day - 30) * 0.0008
                value = 0.005 + drift + noise

            values.append(max(value, 0))

    return timestamps, values


def cusum_detect(
    values: list[float],
    drift: float = 0.5,
    threshold: float = 5.0,
) -> list[int]:
    """
    CUSUM (Cumulative Sum Control Chart) para detecção de changepoints.
    Detecta shifts na média de uma série temporal.
    """
    mean = sum(values[:20]) / 20  # Baseline dos primeiros 20 pontos
    std = math.sqrt(sum((v - mean) ** 2 for v in values[:20]) / 20) or 1.0

    s_pos = 0.0
    s_neg = 0.0
    changepoints = []

    for i, val in enumerate(values):
        normalized = (val - mean) / std
        s_pos = max(0, s_pos + normalized - drift)
        s_neg = max(0, s_neg - normalized - drift)

        if s_pos > threshold or s_neg > threshold:
            changepoints.append(i)
            s_pos = 0.0
            s_neg = 0.0

    return changepoints


def sliding_window_detect(
    values: list[float],
    window: int = 20,
    significance: float = 2.0,
) -> list[int]:
    """
    Detecção por janela deslizante — compara média de duas janelas
    consecutivas e detecta shifts significativos.
    """
    changepoints = []

    for i in range(window, len(values) - window):
        left = values[i - window:i]
        right = values[i:i + window]

        mean_left = sum(left) / len(left)
        mean_right = sum(right) / len(right)

        std_left = math.sqrt(sum((v - mean_left) ** 2 for v in left) / len(left)) or 1.0

        if abs(mean_right - mean_left) > significance * std_left:
            # Evitar detecções consecutivas
            if not changepoints or i - changepoints[-1] > window:
                changepoints.append(i)

    return changepoints


def analyze_changepoint(
    timestamps: list[datetime],
    values: list[float],
    cp_index: int,
    metric_name: str,
    window: int = 20,
) -> Changepoint:
    """Analisa um changepoint detectado."""
    before = values[max(0, cp_index - window):cp_index]
    after = values[cp_index:min(len(values), cp_index + window)]

    mean_before = sum(before) / len(before) if before else 0
    mean_after = sum(after) / len(after) if after else 0

    shift = mean_after - mean_before
    shift_pct = (shift / mean_before * 100) if mean_before != 0 else 0

    std_before = math.sqrt(sum((v - mean_before) ** 2 for v in before) / len(before)) if before else 1
    confidence = min(abs(shift) / std_before / 3, 1.0) if std_before > 0 else 0.5

    return Changepoint(
        index=cp_index,
        timestamp=timestamps[cp_index],
        metric=metric_name,
        mean_before=mean_before,
        mean_after=mean_after,
        shift_magnitude=shift,
        shift_pct=shift_pct,
        confidence=confidence,
    )


def sparkline(values: list[float], width: int = 60) -> str:
    chars = "▁▂▃▄▅▆▇█"
    step = max(1, len(values) // width)
    sampled = [values[i] for i in range(0, len(values), step)][:width]
    mn, mx = min(sampled), max(sampled)
    rng = mx - mn if mx != mn else 1
    return "".join(chars[int((v - mn) / rng * (len(chars) - 1))] for v in sampled)


def run_demo() -> None:
    print("=" * 70)
    print("🔍 Demo: Detectando Desvios em Métricas Operacionais")
    print("   Curso 3 — Observabilidade Inteligente")
    print("=" * 70)

    # === Cenário 1: Latência com shift abrupto ===
    print(f"\n{'─' * 70}")
    print("📊 CENÁRIO 1: Latência p99 do checkout-service")
    print(f"{'─' * 70}")
    print("  Threshold estático configurado: 500ms")
    print("  → Esse threshold NÃO detectaria o problema!\n")

    ts1, vals1 = generate_latency_with_shift()
    print(f"  Série: {sparkline(vals1)}")
    print(f"  Min: {min(vals1):.0f}ms  Max: {max(vals1):.0f}ms")

    cp_indices = sliding_window_detect(vals1)
    if cp_indices:
        print(f"\n  🎯 Changepoints detectados: {len(cp_indices)}")
        for idx in cp_indices:
            cp = analyze_changepoint(ts1, vals1, idx, "latency_p99_ms")
            print(f"\n  📍 Changepoint em {cp.timestamp.strftime('%d/%m/%Y')}")
            print(f"     Antes : {cp.mean_before:.1f}ms (±baseline)")
            print(f"     Depois: {cp.mean_after:.1f}ms")
            print(f"     Shift : {cp.shift_magnitude:+.1f}ms ({cp.shift_pct:+.1f}%)")
            print(f"     Confiança: {cp.confidence:.0%}")
            print(f"     ⚠️  Latência subiu {cp.shift_pct:.0f}% — threshold estático não alarmou!")

    # === Cenário 2: Error rate com drift gradual ===
    print(f"\n{'─' * 70}")
    print("📊 CENÁRIO 2: Error rate do payment-service (drift gradual)")
    print(f"{'─' * 70}")
    print("  Threshold estático: 5%")
    print("  → O drift lento escapa do threshold por semanas!\n")

    ts2, vals2 = generate_error_rate_with_gradual_drift()
    print(f"  Série: {sparkline(vals2)}")
    print(f"  Min: {min(vals2):.4f}  Max: {max(vals2):.4f}")

    cp_indices2 = cusum_detect(vals2, drift=0.3, threshold=4.0)
    if cp_indices2:
        print(f"\n  🎯 Changepoints CUSUM detectados: {len(cp_indices2)}")
        for idx in cp_indices2[:3]:
            if idx < len(ts2):
                cp = analyze_changepoint(ts2, vals2, idx, "error_rate")
                print(f"\n  📍 Drift detectado em {cp.timestamp.strftime('%d/%m/%Y')}")
                print(f"     Antes : {cp.mean_before:.4f} ({cp.mean_before * 100:.2f}%)")
                print(f"     Depois: {cp.mean_after:.4f} ({cp.mean_after * 100:.2f}%)")
                print(f"     ⚠️  Error rate dobrando — CUSUM detectou antes do threshold!")

    # Resumo
    print("\n" + "=" * 70)
    print("📋 COMPARATIVO: THRESHOLD ESTÁTICO vs. CHANGEPOINT DETECTION")
    print("=" * 70)

    print(f"""
  {'Aspecto':<30} {'Threshold Estático':<25} {'Changepoint Detection':<25}
  {'─' * 30} {'─' * 25} {'─' * 25}
  {'Latência 120→165ms':<30} {'Não alerta (< 500ms)':<25} {'✅ Detecta shift':<25}
  {'Error rate drift lento':<30} {'Alerta tarde demais':<25} {'✅ Detecta drift cedo':<25}
  {'Picos sazonais normais':<30} {'Pode alarmar falso':<25} {'✅ Ignora (é padrão)':<25}
  {'Configuração':<30} {'Manual e rígido':<25} {'Adapta-se aos dados':<25}
    """)

    print("=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  Thresholds estáticos são cegos para mudanças de regime.
  Técnicas como CUSUM e janela deslizante detectam shifts
  na média antes que eles causem um incidente visível.

  Na Aula 2.5 (Hands-on), vamos construir modelos preditivos
  completos aplicados a um cluster operacional.
    """)


if __name__ == "__main__":
    run_demo()
