"""
Vídeo 2.5 — Hands-on: Análise de tendências e previsão operacional
====================================================================
EXERCÍCIO PRÁTICO — Aula 2

Neste hands-on você vai analisar um cluster operacional completo,
combinando todas as técnicas da Aula 2:
  1. Análise de tendências (2.1)
  2. Previsão de saturação (2.2)
  3. Decomposição sazonal (2.3)
  4. Detecção de changepoints (2.4)

Cenário:
  Você é o SRE responsável pelo cluster "prod-east-01" que roda
  12 microsserviços. O time de engenharia pede um relatório de
  capacity planning para os próximos 90 dias.

Execute:
  python trend_prediction_lab.py
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class ClusterResource:
    name: str
    unit: str
    capacity: float
    samples: list[tuple[datetime, float]]


@dataclass
class PredictionResult:
    resource: str
    current: float
    capacity: float
    trend_slope: float
    days_to_80pct: float | None
    days_to_full: float | None
    has_changepoint: bool
    anomaly_count: int
    risk: str


def linreg(x: list[float], y: list[float]) -> tuple[float, float, float]:
    n = len(x)
    if n < 2:
        return 0.0, y[0] if y else 0.0, 0.0
    sx, sy = sum(x), sum(y)
    sxy = sum(a * b for a, b in zip(x, y))
    sx2 = sum(a ** 2 for a in x)
    d = n * sx2 - sx ** 2
    if d == 0:
        return 0.0, sy / n, 0.0
    sl = (n * sxy - sx * sy) / d
    it = (sy - sl * sx) / n
    my = sy / n
    ss_tot = sum((yi - my) ** 2 for yi in y)
    ss_res = sum((yi - (sl * xi + it)) ** 2 for xi, yi in zip(x, y))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return sl, it, r2


def cusum(values: list[float], drift: float = 0.5, thresh: float = 5.0) -> list[int]:
    if len(values) < 20:
        return []
    base = values[:20]
    mean = sum(base) / len(base)
    std = math.sqrt(sum((v - mean) ** 2 for v in base) / len(base)) or 1.0
    sp, sn = 0.0, 0.0
    cps = []
    for i, v in enumerate(values):
        norm = (v - mean) / std
        sp = max(0, sp + norm - drift)
        sn = max(0, sn - norm - drift)
        if sp > thresh or sn > thresh:
            cps.append(i)
            sp, sn = 0.0, 0.0
    return cps


def detect_residual_anomalies(values: list[float], window: int = 24) -> int:
    if len(values) < window * 2:
        return 0
    trend = []
    for i in range(len(values)):
        s = max(0, i - window // 2)
        e = min(len(values), i + window // 2 + 1)
        trend.append(sum(values[s:e]) / (e - s))
    residuals = [v - t for v, t in zip(values, trend)]
    mean_r = sum(residuals) / len(residuals)
    std_r = math.sqrt(sum((r - mean_r) ** 2 for r in residuals) / len(residuals)) or 1.0
    return sum(1 for r in residuals if abs(r - mean_r) > 2.5 * std_r)


def generate_cluster_data() -> list[ClusterResource]:
    base = datetime(2024, 5, 1)
    resources = []

    # CPU cluster
    cpu = ClusterResource("cpu_utilization", "%", 100.0, [])
    for d in range(90):
        for h in [0, 6, 12, 18]:
            hourly = 0.15 * math.sin(h * math.pi / 12)  # Padrão diário
            val = 55 + d * 0.25 + hourly * 10 + (hash(str(d * 4 + h // 6)) % 10 - 5)
            cpu.samples.append((base + timedelta(days=d, hours=h), min(val, 100)))
    resources.append(cpu)

    # Memória
    mem = ClusterResource("memory_used", "GB", 256.0, [])
    for d in range(90):
        val = 145 + d * 0.85 + (hash(str(d + 100)) % 12 - 6)
        mem.samples.append((base + timedelta(days=d), val))
    resources.append(mem)

    # Disco (PVC)
    disk = ClusterResource("pvc_usage", "GB", 500.0, [])
    for d in range(90):
        val = 280 + d * 1.8 + (hash(str(d + 200)) % 15 - 7)
        disk.samples.append((base + timedelta(days=d), min(val, 500)))
    resources.append(disk)

    # Pods running
    pods = ClusterResource("pods_running", "pods", 150.0, [])
    for d in range(90):
        # Changepoint no dia 50 (novo deployment escalou pods)
        base_pods = 78 if d < 50 else 105
        val = base_pods + (hash(str(d + 300)) % 8 - 4)
        pods.samples.append((base + timedelta(days=d), val))
    resources.append(pods)

    # Network egress
    net = ClusterResource("network_egress", "Mbps", 5000.0, [])
    for d in range(90):
        daily = 200 * math.sin(d * 2 * math.pi / 7)  # Padrão semanal
        val = 2100 + d * 15 + daily + (hash(str(d + 400)) % 50 - 25)
        net.samples.append((base + timedelta(days=d), val))
    resources.append(net)

    return resources


def analyze_resource(res: ClusterResource) -> PredictionResult:
    base_ts = res.samples[0][0]
    x = [(s[0] - base_ts).total_seconds() / 86400 for s in res.samples]
    y = [s[1] for s in res.samples]

    slope, intercept, r2 = linreg(x, y)
    current = y[-1]
    current_day = x[-1]

    def days_to(level: float) -> float | None:
        target = res.capacity * level
        if slope <= 0 or current >= target:
            return 0.0 if current >= target else None
        projected = slope * current_day + intercept
        return (target - projected) / slope if slope > 0 else None

    d80 = days_to(0.80)
    dfull = days_to(1.0)

    cps = cusum(y)
    anom = detect_residual_anomalies(y)

    if dfull is not None and dfull < 14:
        risk = "CRITICAL"
    elif dfull is not None and dfull < 45:
        risk = "HIGH"
    elif d80 is not None and d80 < 30:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return PredictionResult(
        resource=res.name, current=current, capacity=res.capacity,
        trend_slope=slope, days_to_80pct=d80, days_to_full=dfull,
        has_changepoint=len(cps) > 0, anomaly_count=anom, risk=risk,
    )


def sparkline(values: list[float], w: int = 50) -> str:
    chars = "▁▂▃▄▅▆▇█"
    step = max(1, len(values) // w)
    s = [values[i] for i in range(0, len(values), step)][:w]
    mn, mx = min(s), max(s)
    r = mx - mn if mx != mn else 1
    return "".join(chars[int((v - mn) / r * 7)] for v in s)


def run_lab() -> None:
    print("=" * 70)
    print("🔬 HANDS-ON: Análise de Tendências e Previsão Operacional")
    print("   Curso 3 — Observabilidade Inteligente — Aula 2")
    print("=" * 70)
    print("\n  📋 Cluster: prod-east-01 (12 microsserviços)")
    print("  📅 Período analisado: 90 dias de dados históricos")
    print("  🎯 Objetivo: Relatório de Capacity Planning")
    time.sleep(0.3)

    resources = generate_cluster_data()
    results: list[PredictionResult] = []

    # PASSO 1: Análise individual
    print("\n" + "─" * 70)
    print("PASSO 1/3 — Análise individual de cada recurso")
    print("─" * 70)

    for res in resources:
        values = [s[1] for s in res.samples]
        print(f"\n  📊 {res.name} ({res.unit})")
        print(f"     {sparkline(values)}")
        print(f"     Atual: {values[-1]:.1f}/{res.capacity:.0f} {res.unit} "
              f"({values[-1] / res.capacity * 100:.1f}%)")

        result = analyze_resource(res)
        results.append(result)

        print(f"     Crescimento: +{result.trend_slope:.2f} {res.unit}/dia")
        if result.has_changepoint:
            print(f"     ⚡ Changepoint detectado na série!")
        if result.anomaly_count > 0:
            print(f"     ⚠️  {result.anomaly_count} anomalias no resíduo")
    time.sleep(0.3)

    # PASSO 2: Forecast
    print("\n" + "─" * 70)
    print("PASSO 2/3 — Forecast de saturação (próximos 90 dias)")
    print("─" * 70)

    today = datetime(2024, 7, 30)

    for r in results:
        risk_icons = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
        print(f"\n  {risk_icons[r.risk]} {r.resource}")

        if r.days_to_80pct is not None and r.days_to_80pct > 0:
            date_80 = today + timedelta(days=r.days_to_80pct)
            print(f"     Warning (80%): {r.days_to_80pct:.0f} dias ({date_80.strftime('%d/%m/%Y')})")
        elif r.days_to_80pct == 0:
            print(f"     Warning (80%): ⚠️ JÁ ATINGIDO")

        if r.days_to_full is not None and r.days_to_full > 0:
            date_full = today + timedelta(days=r.days_to_full)
            print(f"     Full (100%) : {r.days_to_full:.0f} dias ({date_full.strftime('%d/%m/%Y')})")
        elif r.days_to_full == 0:
            print(f"     Full (100%) : 🔴 JÁ ATINGIDO")
        else:
            print(f"     Full (100%) : sem risco previsto")
    time.sleep(0.3)

    # PASSO 3: Relatório
    print("\n" + "=" * 70)
    print("PASSO 3/3 — RELATÓRIO DE CAPACITY PLANNING")
    print("=" * 70)

    results.sort(key=lambda r: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}[r.risk])

    print(f"\n  {'Recurso':<25} {'Uso Atual':<12} {'Crescimento':<15} {'Saturação':<12} {'Risco':<10}")
    print(f"  {'─' * 25} {'─' * 12} {'─' * 15} {'─' * 12} {'─' * 10}")
    for r in results:
        uso = f"{r.current / r.capacity * 100:.0f}%"
        cresc = f"+{r.trend_slope:.2f}/d"
        sat = f"{r.days_to_full:.0f}d" if r.days_to_full and r.days_to_full > 0 else "N/A"
        risk_icons = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
        print(f"  {r.resource:<25} {uso:<12} {cresc:<15} {sat:<12} {risk_icons[r.risk]} {r.risk}")

    critical_count = sum(1 for r in results if r.risk in ("CRITICAL", "HIGH"))
    print(f"\n  📊 SUMÁRIO EXECUTIVO:")
    print(f"     Recursos analisados : {len(results)}")
    print(f"     Riscos altos/críticos: {critical_count}")
    print(f"     Changepoints detectados: {sum(1 for r in results if r.has_changepoint)}")
    print(f"     Anomalias totais    : {sum(r.anomaly_count for r in results)}")

    print(f"\n  ✅ AÇÕES RECOMENDADAS:")
    for r in results:
        if r.risk == "CRITICAL":
            print(f"     🔴 {r.resource}: Expansão URGENTE nos próximos {r.days_to_full:.0f} dias")
        elif r.risk == "HIGH":
            print(f"     🟠 {r.resource}: Planejar expansão para as próximas 4-6 semanas")
        elif r.risk == "MEDIUM":
            print(f"     🟡 {r.resource}: Monitorar tendência — revisitar em 30 dias")

    print("\n" + "=" * 70)
    print("🎓 FIM DO HANDS-ON — AULA 2 CONCLUÍDA!")
    print("=" * 70)
    print("""
  Você aprendeu a:
  ✔ Identificar tendências de crescimento em recursos de infraestrutura
  ✔ Prever datas de saturação com regressão linear
  ✔ Decompor sazonalidade para filtrar picos normais
  ✔ Detectar changepoints sutis com CUSUM
  ✔ Gerar relatórios de capacity planning acionáveis

  Próxima aula: Alertas inteligentes e redução de ruído →
    """)


if __name__ == "__main__":
    run_lab()
