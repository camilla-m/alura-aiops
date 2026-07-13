"""
Vídeo 3.3 — Redução de alert fatigue
======================================
Demonstra estratégias práticas de depuração e consolidação de
alertas para combater a fadiga operacional em equipes SRE.

Conceitos demonstrados:
- Auditoria de alertas: classificação e priorização
- Agrupamento por serviço e causa raiz
- Supressão inteligente (snooze, mute windows)
- Escalonamento baseado em severidade real
- Métricas de qualidade de alertas
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import Counter


@dataclass
class AlertRule:
    """Regra de alerta configurada no sistema."""
    id: str
    name: str
    service: str
    metric: str
    threshold: float
    severity: str  # P1, P2, P3, P4
    fires_per_week: int
    actionable_pct: float  # Percentual que realmente exige ação
    avg_resolution_min: float
    owner_team: str

    @property
    def noise_score(self) -> float:
        """Score de ruído: quanto mais alto, mais inútil o alerta."""
        noise = (1 - self.actionable_pct) * self.fires_per_week
        return round(noise, 1)

    @property
    def category(self) -> str:
        if self.actionable_pct >= 0.8:
            return "ESSENCIAL"
        elif self.actionable_pct >= 0.4:
            return "AJUSTÁVEL"
        elif self.fires_per_week <= 1:
            return "RARO"
        else:
            return "RUÍDO"


def generate_alert_inventory() -> list[AlertRule]:
    """Gera um inventário realista de regras de alerta."""
    return [
        AlertRule("ALR-001", "CPU > 80%", "api-gateway", "cpu_pct", 80, "P2", 28, 0.15, 5, "platform"),
        AlertRule("ALR-002", "Memory > 90%", "user-service", "mem_pct", 90, "P1", 3, 0.90, 25, "backend"),
        AlertRule("ALR-003", "Disk > 85%", "database", "disk_pct", 85, "P1", 2, 0.95, 30, "dba"),
        AlertRule("ALR-004", "Error rate > 1%", "checkout", "error_rate", 1, "P1", 12, 0.35, 15, "backend"),
        AlertRule("ALR-005", "Latency p99 > 2s", "product-svc", "latency_p99", 2000, "P2", 42, 0.08, 3, "backend"),
        AlertRule("ALR-006", "Pod restarts > 3", "notifications", "restarts", 3, "P3", 18, 0.12, 8, "platform"),
        AlertRule("ALR-007", "Queue depth > 1000", "worker-svc", "queue_depth", 1000, "P2", 8, 0.60, 12, "backend"),
        AlertRule("ALR-008", "SSL cert < 30d", "api-gateway", "cert_days", 30, "P3", 1, 0.95, 60, "security"),
        AlertRule("ALR-009", "Health check fail", "cache", "health", 1, "P2", 35, 0.05, 2, "platform"),
        AlertRule("ALR-010", "5xx > 0.5%", "api-gateway", "http_5xx", 0.5, "P1", 15, 0.25, 10, "backend"),
        AlertRule("ALR-011", "Conn pool > 80%", "database", "connections", 80, "P2", 6, 0.70, 20, "dba"),
        AlertRule("ALR-012", "GC pause > 500ms", "analytics", "gc_pause", 500, "P3", 22, 0.10, 4, "data"),
        AlertRule("ALR-013", "Kafka lag > 5000", "event-bus", "consumer_lag", 5000, "P2", 4, 0.80, 15, "platform"),
        AlertRule("ALR-014", "Node not ready", "k8s-cluster", "node_status", 1, "P1", 1, 1.00, 45, "platform"),
        AlertRule("ALR-015", "Deployment failed", "ci-cd", "deploy_status", 1, "P2", 3, 0.85, 30, "devops"),
    ]


@dataclass
class ReductionStrategy:
    """Estratégia de redução aplicada a um alerta."""
    alert_id: str
    action: str  # TUNE, GROUP, SUPPRESS, DOWNGRADE, KEEP, DELETE
    rationale: str
    expected_reduction: int  # Alertas/semana eliminados


def generate_reduction_plan(alerts: list[AlertRule]) -> list[ReductionStrategy]:
    """Gera plano de redução baseado na análise do inventário."""
    strategies = []

    for alert in alerts:
        if alert.category == "RUÍDO" and alert.fires_per_week > 10:
            strategies.append(ReductionStrategy(
                alert.id, "TUNE",
                f"Ajustar threshold de {alert.metric} (apenas {alert.actionable_pct:.0%} acionável)",
                int(alert.fires_per_week * (1 - alert.actionable_pct)),
            ))
        elif alert.category == "RUÍDO" and alert.fires_per_week <= 10:
            strategies.append(ReductionStrategy(
                alert.id, "DELETE",
                f"Excluir — dispara {alert.fires_per_week}x/sem com {alert.actionable_pct:.0%} relevância",
                alert.fires_per_week,
            ))
        elif alert.category == "AJUSTÁVEL":
            strategies.append(ReductionStrategy(
                alert.id, "TUNE",
                f"Refinar threshold: {alert.actionable_pct:.0%} acionável → alvo: 80%+",
                int(alert.fires_per_week * 0.5),
            ))
        elif alert.category == "ESSENCIAL":
            strategies.append(ReductionStrategy(
                alert.id, "KEEP",
                f"Manter — {alert.actionable_pct:.0%} acionável, {alert.fires_per_week}x/sem",
                0,
            ))

    return strategies


def run_demo() -> None:
    print("=" * 70)
    print("🔕 Demo: Redução de Alert Fatigue")
    print("   Curso 3 — Observabilidade Inteligente")
    print("=" * 70)

    alerts = generate_alert_inventory()

    # FASE 1: Auditoria
    print(f"\n{'─' * 70}")
    print("📋 FASE 1: Auditoria do inventário de alertas")
    print(f"{'─' * 70}")

    total_weekly = sum(a.fires_per_week for a in alerts)
    total_actionable = sum(a.fires_per_week * a.actionable_pct for a in alerts)

    print(f"\n  Total de regras configuradas  : {len(alerts)}")
    print(f"  Alertas disparados por semana : {total_weekly}")
    print(f"  Alertas acionáveis por semana : {total_actionable:.0f} ({total_actionable / total_weekly * 100:.0f}%)")
    print(f"  Ruído puro (não acionável)    : {total_weekly - total_actionable:.0f} ({(1 - total_actionable / total_weekly) * 100:.0f}%)")

    # Categorização
    categories = Counter(a.category for a in alerts)
    print(f"\n  Categorização:")
    for cat, count in categories.most_common():
        icons = {"ESSENCIAL": "🟢", "AJUSTÁVEL": "🟡", "RARO": "⚪", "RUÍDO": "🔴"}
        print(f"    {icons[cat]} {cat}: {count} regras")

    # Top ofensores
    print(f"\n  🔴 Top 5 geradores de ruído:")
    noisy = sorted(alerts, key=lambda a: a.noise_score, reverse=True)[:5]
    for a in noisy:
        print(f"    [{a.id}] {a.name:<25} {a.fires_per_week:>3}x/sem  "
              f"acionável: {a.actionable_pct:>4.0%}  ruído: {a.noise_score:.0f}")

    # FASE 2: Plano de redução
    print(f"\n{'─' * 70}")
    print("🔧 FASE 2: Plano de redução")
    print(f"{'─' * 70}")

    strategies = generate_reduction_plan(alerts)
    action_icons = {"TUNE": "🔧", "GROUP": "📦", "SUPPRESS": "🔇",
                    "DOWNGRADE": "⬇️", "KEEP": "✅", "DELETE": "🗑️"}

    for s in strategies:
        alert = next(a for a in alerts if a.id == s.alert_id)
        icon = action_icons.get(s.action, "❓")
        reduction = f"-{s.expected_reduction}/sem" if s.expected_reduction > 0 else "sem mudança"
        print(f"\n  {icon} [{s.alert_id}] {alert.name}")
        print(f"     Ação    : {s.action}")
        print(f"     Razão   : {s.rationale}")
        print(f"     Redução : {reduction}")

    # FASE 3: Projeção
    print(f"\n{'─' * 70}")
    print("📊 FASE 3: Projeção de impacto")
    print(f"{'─' * 70}")

    total_reduction = sum(s.expected_reduction for s in strategies)
    new_total = total_weekly - total_reduction

    print(f"\n  Antes da otimização : {total_weekly} alertas/semana")
    print(f"  Redução projetada   : {total_reduction} alertas/semana")
    print(f"  Depois              : {new_total} alertas/semana")
    print(f"  Redução percentual  : {total_reduction / total_weekly * 100:.0f}%")

    bar_before = "█" * int(total_weekly / 5)
    bar_after = "█" * int(new_total / 5)
    print(f"\n  Antes : {bar_before} ({total_weekly})")
    print(f"  Depois: {bar_after} ({new_total})")

    # Métricas de qualidade
    print(f"\n  📊 Métricas de qualidade de alertas (propostas):")
    print(f"     Signal-to-Noise Ratio : {total_actionable / total_weekly:.0%} → "
          f"{total_actionable / new_total:.0%}")
    print(f"     Alertas por plantão   : {total_weekly / 7:.0f}/dia → {new_total / 7:.0f}/dia")
    print(f"     Interrupções noturnas : ~{total_weekly * 0.3 / 7:.0f} → ~{new_total * 0.3 / 7:.0f}")

    print("\n" + "=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  A redução de alert fatigue não é sobre silenciar alertas — é sobre
  garantir que CADA alerta que dispara merece atenção humana.

  Framework de 3 passos:
  1. AUDITAR: Classificar cada regra por acionabilidade
  2. OTIMIZAR: Ajustar, agrupar ou excluir regras de baixo valor
  3. MEDIR: Acompanhar signal-to-noise ratio continuamente

  Na Aula 3.4, veremos alertas contextuais que consideram
  dependências de topologia para reduzir ainda mais o ruído.
    """)


if __name__ == "__main__":
    run_demo()
