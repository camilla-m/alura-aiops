"""
Vídeo 2.5 — Hands-on: Configurando detecção de anomalias
=========================================================
EXERCÍCIO PRÁTICO — Aula 2

Laboratório completo de criação de monitores inteligentes
com baselines dinâmicos.

O estudante vai:
  1. Carregar uma série temporal de uma métrica real
  2. Comparar detecção estática vs. baseline dinâmico
  3. Configurar o monitor com threshold adaptativo
  4. Gerar o relatório final de anomalias

Execute:
  python smart_monitor_lab.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load(module_name: str, file_path: Path):
    """Carrega um módulo Python pelo caminho absoluto (contorna nomes com hífens)."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


_BASE = Path(__file__).parent.parent

_anomaly_mod  = _load("anomaly_detector",       _BASE / "video-2.1-anomalias-infra"          / "anomaly_detector.py")
_baseline_mod = _load("dynamic_baseline",        _BASE / "video-2.2-baselines-dinamicos"      / "dynamic_baseline.py")
_ts_mod       = _load("time_series_analysis",    _BASE / "video-2.3-series-temporais"         / "time_series_analysis.py")
_fatigue_mod  = _load("alert_fatigue_analyzer",  _BASE / "video-2.4-reducao-alert-fatigue"    / "alert_fatigue_analyzer.py")

generate_cpu_series        = _anomaly_mod.generate_cpu_series
detect_by_static_threshold = _anomaly_mod.detect_by_static_threshold
detect_by_zscore           = _anomaly_mod.detect_by_zscore

DynamicBaseline       = _baseline_mod.DynamicBaseline
report_baseline       = _baseline_mod.report_baseline
generate_weekly_metric = _baseline_mod.generate_weekly_metric

generate_disk_usage_series = _ts_mod.generate_disk_usage_series
forecast_metric            = _ts_mod.forecast_metric
print_forecast_report      = _ts_mod.print_forecast_report

generate_alert_history    = _fatigue_mod.generate_alert_history
analyze_alert_quality     = _fatigue_mod.analyze_alert_quality
print_alert_health_report = _fatigue_mod.print_alert_health_report


def lab_step(step: int, title: str) -> None:
    print(f"\n{'='*65}")
    print(f"  PASSO {step}/4 — {title}")
    print(f"{'='*65}\n")


def run_lab() -> None:
    print("=" * 65)
    print("🧪 LABORATÓRIO: Configurando Detecção de Anomalias")
    print("   Nível 1 — AIOps & Automação de Incidentes")
    print("=" * 65)

    # ------------------------------------------------------------------
    # PASSO 1: Análise de CPU com dois métodos
    # ------------------------------------------------------------------
    lab_step(1, "Comparando threshold estático vs. baseline dinâmico")

    cpu_series = generate_cpu_series(hours=48, inject_anomaly_at=14)

    static_results = detect_by_static_threshold(cpu_series, threshold=85.0)
    zscore_results  = detect_by_zscore(cpu_series, z_threshold=2.5)

    static_anomalies = [r for r in static_results if r.is_anomaly]
    zscore_anomalies = [r for r in zscore_results if r.is_anomaly]

    print(f"  Série de CPU: {len(cpu_series)} pontos (48h, 5min de resolução)")
    print(f"\n  Threshold estático (>85%) → {len(static_anomalies)} alertas")
    print(f"  Z-Score dinâmico (>2.5σ)  → {len(zscore_anomalies)} alertas")

    fp_reduction = (len(static_anomalies) - len(zscore_anomalies))
    print(f"\n  ✅ Redução de falsos positivos: ~{fp_reduction} alertas suprimidos")

    # ------------------------------------------------------------------
    # PASSO 2: Baseline dinâmico em série semanal
    # ------------------------------------------------------------------
    lab_step(2, "Treinando baseline dinâmico com sazonalidade semanal")

    rps_series = generate_weekly_metric(days=14)
    baseline = DynamicBaseline(seasonality_period=288, confidence_multiplier=2.5)
    baseline_results = baseline.fit_and_detect(rps_series)
    report_baseline(baseline_results, "requests_per_second")

    # ------------------------------------------------------------------
    # PASSO 3: Forecast de capacidade
    # ------------------------------------------------------------------
    lab_step(3, "Prevendo esgotamento de recursos (capacity planning)")

    disk_series = generate_disk_usage_series(days=30)
    disk_forecast = forecast_metric(disk_series, "disk_usage_pct", threshold=85.0)
    print_forecast_report(disk_forecast)

    # ------------------------------------------------------------------
    # PASSO 4: Auditoria de alertas existentes
    # ------------------------------------------------------------------
    lab_step(4, "Auditando e refatorando regras de alerta existentes")

    records = generate_alert_history(days=30)
    analyses = analyze_alert_quality(records)
    print_alert_health_report(analyses, len(records))

    # ------------------------------------------------------------------
    # Conclusão
    # ------------------------------------------------------------------
    print("\n" + "=" * 65)
    print("🎓 FIM DO HANDS-ON — AULA 2 CONCLUÍDA!")
    print("=" * 65)
    print("""
  Você aprendeu a:
  ✔ Identificar anomalias com métodos estáticos e dinâmicos
  ✔ Implementar baselines adaptativos com sazonalidade
  ✔ Prever esgotamento de recursos com análise de tendência
  ✔ Auditar e refatorar regras de alerta para reduzir ruído

  Próxima aula: Investigação operacional assistida por IA →
    """)


if __name__ == "__main__":
    run_lab()
