"""
Vídeo 3.2 — Baselines dinâmicos e comportamento esperado
=========================================================
Demonstra baselines dinâmicos que adaptam os limites de alerta
ao comportamento histórico real, usando bandas de Bollinger
e desvios estatísticos por período.

Conceitos demonstrados:
- Bandas de Bollinger aplicadas a métricas operacionais
- Baseline por período (hora do dia, dia da semana)
- Desvio padrão como margem adaptativa
- Comparação: threshold estático vs. baseline dinâmico
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class BaselineEntry:
    """Baseline calculado para um período específico."""
    period_key: str  # ex: "mon_10" (segunda às 10h)
    mean: float
    std: float
    upper_band: float  # mean + n*std
    lower_band: float  # mean - n*std
    sample_count: int


@dataclass
class BaselineEvaluation:
    """Resultado da avaliação de um valor contra o baseline."""
    timestamp: datetime
    value: float
    baseline_mean: float
    upper_band: float
    lower_band: float
    is_anomaly: bool
    z_score: float


class DynamicBaselineEngine:
    """Motor de baselines dinâmicos baseado em perfis temporais."""

    def __init__(self, num_deviations: float = 2.5):
        self.num_deviations = num_deviations
        self.profiles: dict[str, list[float]] = {}

    def _period_key(self, ts: datetime) -> str:
        """Gera chave única para o período (dia_da_semana + hora)."""
        day_names = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        return f"{day_names[ts.weekday()]}_{ts.hour:02d}"

    def train(self, history: list[tuple[datetime, float]]) -> None:
        """Treina o baseline com dados históricos."""
        for ts, value in history:
            key = self._period_key(ts)
            self.profiles.setdefault(key, []).append(value)

    def get_baseline(self, ts: datetime) -> BaselineEntry | None:
        """Retorna o baseline para um dado timestamp."""
        key = self._period_key(ts)
        values = self.profiles.get(key, [])

        if len(values) < 3:
            return None

        mean = sum(values) / len(values)
        std = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))

        return BaselineEntry(
            period_key=key,
            mean=mean,
            std=std,
            upper_band=mean + self.num_deviations * std,
            lower_band=max(0, mean - self.num_deviations * std),
            sample_count=len(values),
        )

    def evaluate(self, ts: datetime, value: float) -> BaselineEvaluation:
        """Avalia se um valor está dentro do comportamento esperado."""
        baseline = self.get_baseline(ts)

        if baseline is None:
            return BaselineEvaluation(
                timestamp=ts, value=value,
                baseline_mean=value, upper_band=value * 1.5,
                lower_band=value * 0.5, is_anomaly=False, z_score=0.0,
            )

        z_score = (value - baseline.mean) / baseline.std if baseline.std > 0 else 0.0
        is_anomaly = value > baseline.upper_band or value < baseline.lower_band

        return BaselineEvaluation(
            timestamp=ts, value=value,
            baseline_mean=baseline.mean,
            upper_band=baseline.upper_band,
            lower_band=baseline.lower_band,
            is_anomaly=is_anomaly,
            z_score=z_score,
        )


def generate_training_data(weeks: int = 4) -> list[tuple[datetime, float]]:
    """Gera 4 semanas de dados de treinamento com padrões sazonais."""
    base = datetime(2024, 7, 1)
    data = []

    for week in range(weeks):
        for day in range(7):
            date = base + timedelta(weeks=week, days=day)
            weekday = date.weekday()

            for hour in range(24):
                ts = date.replace(hour=hour)

                # Padrão base
                cpu = 30.0

                # Padrão de horário comercial
                if weekday < 5:
                    if 9 <= hour <= 12:
                        cpu += 35 * math.sin((hour - 9) * math.pi / 3)
                    if 14 <= hour <= 17:
                        cpu += 28 * math.sin((hour - 14) * math.pi / 3)
                    # Batch noturno
                    if hour == 1:
                        cpu += 35

                # Fim de semana
                if weekday >= 5:
                    cpu *= 0.35

                # Ruído natural
                noise = (hash(str(week * 168 + day * 24 + hour)) % 12 - 6)
                data.append((ts, max(cpu + noise, 5)))

    return data


def generate_test_data() -> list[tuple[datetime, float, bool]]:
    """Gera dados de teste com anomalias plantadas."""
    base = datetime(2024, 7, 29)  # Semana seguinte ao treino
    data = []

    for day in range(7):
        date = base + timedelta(days=day)
        weekday = date.weekday()

        for hour in range(24):
            ts = date.replace(hour=hour)
            is_anomaly = False

            cpu = 30.0
            if weekday < 5:
                if 9 <= hour <= 12:
                    cpu += 35 * math.sin((hour - 9) * math.pi / 3)
                if 14 <= hour <= 17:
                    cpu += 28 * math.sin((hour - 14) * math.pi / 3)
                if hour == 1:
                    cpu += 35

            if weekday >= 5:
                cpu *= 0.35

            noise = (hash(str(700 + day * 24 + hour)) % 12 - 6)
            cpu += noise

            # Anomalia 1: CPU alta domingo às 3h (deveria estar baixa)
            if day == 6 and hour == 3:
                cpu = 72
                is_anomaly = True

            # Anomalia 2: CPU baixa quarta às 11h (deveria estar alta)
            if day == 2 and hour == 11:
                cpu = 15
                is_anomaly = True

            # Anomalia 3: Pico gradual terça 14h-16h (memory leak)
            if day == 1 and 14 <= hour <= 16:
                cpu += 25
                is_anomaly = True

            data.append((ts, max(cpu, 5), is_anomaly))

    return data


def run_demo() -> None:
    print("=" * 70)
    print("📏 Demo: Baselines Dinâmicos e Comportamento Esperado")
    print("   Curso 3 — Observabilidade Inteligente")
    print("=" * 70)

    # Treinar baseline
    print(f"\n{'─' * 70}")
    print("📚 FASE 1: Treinamento do baseline (4 semanas de histórico)")
    print(f"{'─' * 70}")

    training_data = generate_training_data()
    engine = DynamicBaselineEngine(num_deviations=2.5)
    engine.train(training_data)

    print(f"\n  Dados de treino: {len(training_data)} amostras")
    print(f"  Períodos aprendidos: {len(engine.profiles)} perfis")
    print(f"  Desvios para banda: {engine.num_deviations}σ")

    # Mostrar alguns perfis
    print(f"\n  Exemplos de perfis aprendidos:")
    for key in ["mon_10", "mon_03", "sat_10", "wed_01"]:
        dt = datetime(2024, 7, 29) + timedelta(days={"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}.get(key[:3], 0), hours=int(key[-2:]))
        bl = engine.get_baseline(dt)
        if bl:
            print(f"    {key}: μ={bl.mean:.1f}  σ={bl.std:.1f}  "
                  f"banda=[{bl.lower_band:.1f}, {bl.upper_band:.1f}]")

    # Avaliar dados de teste
    print(f"\n{'─' * 70}")
    print("🔍 FASE 2: Avaliação contra dados novos (semana 5)")
    print(f"{'─' * 70}")

    test_data = generate_test_data()
    static_threshold = 75.0

    evals = []
    for ts, value, _ in test_data:
        evals.append(engine.evaluate(ts, value))

    detected_anomalies = [e for e in evals if e.is_anomaly]
    static_alerts = [(ts, v) for ts, v, _ in test_data if v > static_threshold]

    print(f"\n  Resultados:")
    print(f"    Anomalias pelo baseline dinâmico: {len(detected_anomalies)}")
    print(f"    Alertas pelo threshold estático ({static_threshold}%): {len(static_alerts)}")

    print(f"\n  Anomalias detectadas pelo baseline dinâmico:")
    for e in detected_anomalies:
        direction = "ACIMA" if e.value > e.upper_band else "ABAIXO"
        print(f"    [{e.timestamp.strftime('%a %H:%M')}] CPU={e.value:.1f}%  "
              f"esperado=[{e.lower_band:.1f}, {e.upper_band:.1f}]  "
              f"z={e.z_score:+.1f}  {direction}")

    # Comparação visual
    print(f"\n{'─' * 70}")
    print("📊 COMPARATIVO: Dia de exemplo (terça-feira)")
    print(f"{'─' * 70}")

    tuesday_data = [(ts, v, a) for ts, v, a in test_data if ts.weekday() == 1]

    print(f"\n  Hora  Valor  Banda           Estático  Dinâmico  Real")
    print(f"  ────  ─────  ──────────────  ────────  ────────  ────")

    for ts, value, is_real_anomaly in tuesday_data:
        ev = engine.evaluate(ts, value)
        static_alert = "⚡" if value > static_threshold else "  "
        dynamic_alert = "⚡" if ev.is_anomaly else "  "
        real = "🎯" if is_real_anomaly else "  "

        print(f"  {ts.strftime('%H')}h   {value:>5.1f}  "
              f"[{ev.lower_band:>5.1f},{ev.upper_band:>5.1f}]  "
              f"   {static_alert}       {dynamic_alert}       {real}")

    print(f"""
  Legenda: ⚡ = alerta disparado  🎯 = anomalia real

  O baseline dinâmico detecta:
  ✅ CPU de 72% no domingo às 3h (deveria ser ~12%)
  ✅ CPU de 15% na quarta às 11h (deveria ser ~55%)
  ✅ Pico anômalo na terça 14-16h (acima da banda esperada)

  O threshold estático (75%):
  ❌ Ignora a CPU baixa anômala (15% < 75%)
  ❌ Ignora picos dentro do threshold mas fora do padrão
    """)

    print("=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  Baselines dinâmicos aprendem "o que é normal" para cada momento.
  Segunda às 10h tem um baseline diferente de domingo às 3h.
  Isso elimina falsos positivos em picos normais e detecta
  anomalias que thresholds fixos nunca perceberiam.

  Na Aula 3.3, veremos estratégias para reduzir a alert fatigue
  quando ainda temos muitos alertas legítimos.
    """)


if __name__ == "__main__":
    run_demo()
