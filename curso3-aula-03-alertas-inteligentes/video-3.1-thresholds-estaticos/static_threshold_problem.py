"""
Vídeo 3.1 — O problema dos thresholds estáticos
=================================================
Demonstra por que limites fixos tradicionais falham em ambientes
de microsserviços dinâmicos, gerando falsos positivos durante
picos normais e falsos negativos em degradações sutis.

Conceitos demonstrados:
- Falsos positivos: alertas em picos sazonais normais
- Falsos negativos: degradações abaixo do threshold
- Custo operacional da fadiga de alertas
- O paradoxo do threshold: muito alto ignora, muito baixo alarma
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class AlertEvent:
    timestamp: datetime
    metric: str
    value: float
    threshold: float
    is_actionable: bool  # Se realmente precisava de ação
    classification: str  # "TRUE_POSITIVE", "FALSE_POSITIVE", "FALSE_NEGATIVE"

    def __str__(self) -> str:
        icons = {
            "TRUE_POSITIVE": "🔴 REAL",
            "FALSE_POSITIVE": "🟡 FALSO",
            "FALSE_NEGATIVE": "⚫ PERDIDO",
        }
        return (
            f"  [{self.timestamp.strftime('%a %H:%M')}] "
            f"{icons[self.classification]:>12} "
            f"{self.metric}: {self.value:.1f} (threshold: {self.threshold:.1f})"
        )


def generate_realistic_cpu_data() -> list[tuple[datetime, float, bool]]:
    """
    Gera dados de CPU com padrões reais:
    - Picos diários às 10h-12h e 14h-16h (horário comercial)
    - Batch jobs à 1h (pico noturno normal)
    - Uma degradação real sutil no dia 5
    """
    base = datetime(2024, 8, 5)  # Segunda-feira
    data = []

    for day in range(7):
        date = base + timedelta(days=day)
        weekday = date.weekday()

        for hour in range(24):
            ts = date.replace(hour=hour)

            # Base load
            cpu = 35.0

            # Padrão de horário comercial (seg-sex)
            if weekday < 5:
                if 9 <= hour <= 12:
                    cpu += 30 * math.sin((hour - 9) * math.pi / 3)
                if 14 <= hour <= 17:
                    cpu += 25 * math.sin((hour - 14) * math.pi / 3)

            # Batch job noturno (todo dia à 1h)
            if hour == 1:
                cpu += 40

            # Fim de semana — load reduzido
            if weekday >= 5:
                cpu *= 0.4

            # Degradação real sutil no dia 5 (quarta) — leak de memória
            # causa aumento de ~15% que threshold de 85% não pega
            is_real_problem = False
            if day >= 4 and weekday < 5:
                cpu += 12
                if 10 <= hour <= 16:
                    is_real_problem = True  # Deveria alertar

            # Ruído
            noise = (hash(str(day * 24 + hour)) % 10 - 5)
            cpu += noise

            data.append((ts, max(cpu, 5), is_real_problem))

    return data


def evaluate_static_threshold(
    data: list[tuple[datetime, float, bool]], threshold: float
) -> list[AlertEvent]:
    """Avalia um threshold estático contra os dados."""
    alerts = []

    for ts, value, is_problem in data:
        triggered = value > threshold

        if triggered and is_problem:
            classification = "TRUE_POSITIVE"
        elif triggered and not is_problem:
            classification = "FALSE_POSITIVE"
        elif not triggered and is_problem:
            classification = "FALSE_NEGATIVE"
        else:
            continue  # Sem alerta, sem problema — correto

        alerts.append(AlertEvent(
            timestamp=ts, metric="cpu_utilization_%",
            value=value, threshold=threshold,
            is_actionable=is_problem,
            classification=classification,
        ))

    return alerts


def run_demo() -> None:
    print("=" * 70)
    print("⚠️  Demo: O Problema dos Thresholds Estáticos")
    print("   Curso 3 — Observabilidade Inteligente")
    print("=" * 70)

    data = generate_realistic_cpu_data()
    values = [d[1] for d in data]

    # Visualização do padrão
    print(f"\n{'─' * 70}")
    print("📊 CPU Utilization — 1 semana (cluster prod-east-01)")
    print(f"{'─' * 70}")

    for day_offset in range(7):
        base = datetime(2024, 8, 5) + timedelta(days=day_offset)
        day_name = base.strftime('%a')
        day_values = [d[1] for d in data if d[0].date() == base.date()]

        if day_values:
            chars = "▁▂▃▄▅▆▇█"
            mn, mx = min(values), max(values)
            rng = mx - mn if mx != mn else 1
            line = "".join(chars[int((v - mn) / rng * 7)] for v in day_values)
            print(f"  {day_name}: {line} (max: {max(day_values):.0f}%)")

    # Testar diferentes thresholds
    thresholds = [60.0, 70.0, 80.0, 85.0]

    for thresh in thresholds:
        alerts = evaluate_static_threshold(data, thresh)

        tp = sum(1 for a in alerts if a.classification == "TRUE_POSITIVE")
        fp = sum(1 for a in alerts if a.classification == "FALSE_POSITIVE")
        fn = sum(1 for a in alerts if a.classification == "FALSE_NEGATIVE")
        total_real = sum(1 for _, _, p in data if p)

        print(f"\n{'─' * 70}")
        print(f"🔔 THRESHOLD = {thresh:.0f}%")
        print(f"{'─' * 70}")

        if alerts:
            for a in alerts[:8]:
                print(a)
            if len(alerts) > 8:
                print(f"  ... +{len(alerts) - 8} alertas adicionais")

        precision = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0
        recall = tp / total_real * 100 if total_real > 0 else 0

        print(f"\n  📊 Métricas:")
        print(f"     True Positives  : {tp:>3} (alertas reais acionáveis)")
        print(f"     False Positives : {fp:>3} (alarmes falsos → fadiga!)")
        print(f"     False Negatives : {fn:>3} (problemas ignorados!)")
        print(f"     Precisão        : {precision:.0f}%")
        print(f"     Recall          : {recall:.0f}%")

    # Tabela comparativa
    print("\n" + "=" * 70)
    print("📋 COMPARATIVO DE THRESHOLDS")
    print("=" * 70)

    print(f"\n  {'Threshold':<12} {'Alertas':<10} {'Falsos+':<10} {'Perdidos':<10} {'Precisão':<10} {'Veredicto':<15}")
    print(f"  {'─' * 12} {'─' * 10} {'─' * 10} {'─' * 10} {'─' * 10} {'─' * 15}")

    for thresh in thresholds:
        alerts = evaluate_static_threshold(data, thresh)
        tp = sum(1 for a in alerts if a.classification == "TRUE_POSITIVE")
        fp = sum(1 for a in alerts if a.classification == "FALSE_POSITIVE")
        fn = sum(1 for a in alerts if a.classification == "FALSE_NEGATIVE")
        prec = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0
        total = tp + fp

        if fp > tp:
            verdict = "❌ Muito ruído"
        elif fn > tp:
            verdict = "❌ Perde problemas"
        else:
            verdict = "⚠️  Compromisso"

        print(f"  {thresh:<12.0f} {total:<10} {fp:<10} {fn:<10} {prec:<10.0f}% {verdict:<15}")

    print(f"""
  💡 PARADOXO DO THRESHOLD ESTÁTICO:
     - Threshold BAIXO (60%) → Pega tudo, mas acorda o time toda noite
     - Threshold ALTO (85%)  → Silêncio, mas perde degradações reais
     - Não existe valor "perfeito" — o problema é o modelo, não o número
    """)

    print("=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  Thresholds estáticos tratam todos os momentos como iguais.
  CPU de 75% às 10h de segunda é NORMAL (pico comercial).
  CPU de 75% às 3h de domingo é ANORMAL (deveria estar em 15%).

  Na Aula 3.2, veremos como baselines dinâmicos resolvem isso
  adaptando o limite ao comportamento histórico de cada período.
    """)


if __name__ == "__main__":
    run_demo()
