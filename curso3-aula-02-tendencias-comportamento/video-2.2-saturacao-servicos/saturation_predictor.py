"""
Vídeo 2.2 — Antecipando saturação e degradação de serviços
===========================================================
Demonstra previsão de saturação usando regressão em dados
históricos. Prevê janelas temporais de quebra operacional
para evitar incidentes por esgotamento de recursos.

Conceitos demonstrados:
- Modelagem preditiva para capacidade de infraestrutura
- Regressão linear com intervalos de confiança
- Projeção de saturação de múltiplos recursos simultaneamente
- Classificação de risco e priorização de ações
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class ResourceMetric:
    """Métrica de um recurso com limites de capacidade."""
    name: str
    service: str
    unit: str
    capacity: float
    warning_pct: float = 0.80
    critical_pct: float = 0.90
    samples: list[tuple[datetime, float]] = field(default_factory=list)


@dataclass
class SaturationForecast:
    """Previsão de saturação de um recurso."""
    resource: str
    service: str
    current_utilization_pct: float
    slope_per_day: float
    r_squared: float
    days_to_warning: float | None
    days_to_critical: float | None
    days_to_full: float | None
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    confidence: str  # LOW, MEDIUM, HIGH


def linear_regression(x: list[float], y: list[float]) -> tuple[float, float, float]:
    """Regressão linear: retorna (slope, intercept, r_squared)."""
    n = len(x)
    if n < 2:
        return 0.0, y[0] if y else 0.0, 0.0
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(a * b for a, b in zip(x, y))
    sum_x2 = sum(a ** 2 for a in x)
    denom = n * sum_x2 - sum_x ** 2
    if denom == 0:
        return 0.0, sum_y / n, 0.0
    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    mean_y = sum_y / n
    ss_tot = sum((yi - mean_y) ** 2 for yi in y)
    ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, y))
    r_sq = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    return slope, intercept, r_sq


def generate_resource_data() -> list[ResourceMetric]:
    """Gera dados históricos para múltiplos recursos."""
    base = datetime(2024, 4, 1)
    resources = []

    # 1. Disco — crescimento constante (perigoso)
    disk = ResourceMetric("disk_usage", "storage-cluster", "GB", 2000.0)
    for d in range(60):
        val = 1200 + d * 8.5 + (hash(str(d)) % 20 - 10)
        disk.samples.append((base + timedelta(days=d), val))
    resources.append(disk)

    # 2. Memória — crescimento lento (leak)
    mem = ResourceMetric("memory_rss", "order-service", "%", 100.0)
    for d in range(60):
        val = 52 + d * 0.45 + (hash(str(d + 500)) % 8 - 4) * 0.3
        mem.samples.append((base + timedelta(days=d), min(val, 100)))
    resources.append(mem)

    # 3. Conexões DB — estável
    conn = ResourceMetric("db_connections", "postgres-primary", "conn", 200.0)
    for d in range(60):
        val = 85 + (hash(str(d + 1000)) % 30 - 15)
        conn.samples.append((base + timedelta(days=d), val))
    resources.append(conn)

    # 4. File descriptors — crescimento acelerado
    fd = ResourceMetric("open_file_descriptors", "log-collector", "fd", 65536.0)
    for d in range(60):
        val = 30000 + d * 450 + (hash(str(d + 2000)) % 200 - 100)
        fd.samples.append((base + timedelta(days=d), val))
    resources.append(fd)

    # 5. Network bandwidth — crescimento moderado
    bw = ResourceMetric("network_egress", "cdn-proxy", "Mbps", 10000.0)
    for d in range(60):
        val = 4200 + d * 35 + (hash(str(d + 3000)) % 100 - 50)
        bw.samples.append((base + timedelta(days=d), val))
    resources.append(bw)

    return resources


def forecast_saturation(resource: ResourceMetric) -> SaturationForecast:
    """Calcula a previsão de saturação para um recurso."""
    base_ts = resource.samples[0][0]
    x = [(s[0] - base_ts).total_seconds() / 86400 for s in resource.samples]
    y = [s[1] for s in resource.samples]

    slope, intercept, r_sq = linear_regression(x, y)

    current = y[-1]
    current_pct = current / resource.capacity * 100
    current_day = x[-1]

    def days_to_level(level_pct: float) -> float | None:
        target = resource.capacity * level_pct
        if slope <= 0 or current >= target:
            return None if slope <= 0 else 0.0
        return (target - (slope * current_day + intercept)) / slope

    d_warn = days_to_level(resource.warning_pct)
    d_crit = days_to_level(resource.critical_pct)
    d_full = days_to_level(1.0)

    # Classificar risco
    if d_full is not None and d_full < 7:
        risk = "CRITICAL"
    elif d_crit is not None and d_crit < 14:
        risk = "HIGH"
    elif d_warn is not None and d_warn < 30:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    confidence = "HIGH" if r_sq > 0.85 else "MEDIUM" if r_sq > 0.6 else "LOW"

    return SaturationForecast(
        resource=resource.name,
        service=resource.service,
        current_utilization_pct=current_pct,
        slope_per_day=slope,
        r_squared=r_sq,
        days_to_warning=d_warn,
        days_to_critical=d_crit,
        days_to_full=d_full,
        risk_level=risk,
        confidence=confidence,
    )


def render_gauge(pct: float, width: int = 40) -> str:
    """Renderiza um gauge bar com cores baseadas no percentual."""
    filled = int(pct / 100 * width)
    empty = width - filled
    if pct >= 90:
        icon = "🔴"
    elif pct >= 80:
        icon = "🟡"
    else:
        icon = "🟢"
    return f"{icon} [{'█' * filled}{'░' * empty}] {pct:.1f}%"


def run_demo() -> None:
    print("=" * 70)
    print("🔮 Demo: Antecipando Saturação e Degradação de Serviços")
    print("   Curso 3 — Observabilidade Inteligente")
    print("=" * 70)

    resources = generate_resource_data()
    forecasts: list[SaturationForecast] = []

    for res in resources:
        print(f"\n{'─' * 70}")
        print(f"📊 {res.name} ({res.service})")
        print(f"{'─' * 70}")

        fc = forecast_saturation(res)
        forecasts.append(fc)

        print(f"\n  Utilização atual: {render_gauge(fc.current_utilization_pct)}")
        print(f"  Capacidade      : {res.capacity:.0f} {res.unit}")
        print(f"  Crescimento     : +{fc.slope_per_day:.1f} {res.unit}/dia")
        print(f"  Confiança (R²)  : {fc.r_squared:.3f} ({fc.confidence})")

        print(f"\n  Projeção de esgotamento:")
        for label, days in [("Warning (80%)", fc.days_to_warning),
                            ("Critical (90%)", fc.days_to_critical),
                            ("Full (100%)", fc.days_to_full)]:
            if days is not None and days > 0:
                target_date = datetime(2024, 5, 31) + timedelta(days=days)
                print(f"    {label:<18}: {days:>5.0f} dias ({target_date.strftime('%d/%m/%Y')})")
            elif days is not None and days <= 0:
                print(f"    {label:<18}: ⚠️ JÁ ULTRAPASSADO")
            else:
                print(f"    {label:<18}: sem tendência de atingir")

        risk_icons = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
        print(f"\n  Risco: {risk_icons[fc.risk_level]} {fc.risk_level}")

    # Resumo executivo
    print("\n" + "=" * 70)
    print("📋 PAINEL DE CAPACITY PLANNING")
    print("=" * 70)

    forecasts.sort(key=lambda f: (
        {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}[f.risk_level],
        f.days_to_full or 9999,
    ))

    print(f"\n  {'Recurso':<28} {'Serviço':<20} {'Uso':<8} {'Saturação':<12} {'Risco':<10}")
    print(f"  {'─' * 28} {'─' * 20} {'─' * 8} {'─' * 12} {'─' * 10}")
    for fc in forecasts:
        days_str = f"{fc.days_to_full:.0f}d" if fc.days_to_full and fc.days_to_full > 0 else "N/A"
        risk_icons = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
        print(f"  {fc.resource:<28} {fc.service:<20} {fc.current_utilization_pct:>5.1f}% {days_str:>12} "
              f"{risk_icons[fc.risk_level]} {fc.risk_level}")

    print("\n" + "=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  A previsão de saturação transforma o capacity planning de reativo
  em proativo. Com 60 dias de dados históricos e regressão simples,
  conseguimos prever com semanas de antecedência quais recursos
  precisam de expansão — antes que causem um incidente.

  Na Aula 2.3, veremos como a decomposição sazonal diferencia
  picos normais de variações anômalas nas séries temporais.
    """)


if __name__ == "__main__":
    run_demo()
