"""
Vídeo 1.1 — O problema do alert storm em ambientes modernos
===========================================================
Simulação de um alert storm em cascata para demonstrar como
um único ponto de falha pode gerar dezenas de alertas secundários
em uma arquitetura de microsserviços.

Conceitos demonstrados:
- Propagação de falhas em cascata
- Ruído operacional vs. alertas acionáveis
- Alert grouping básico
"""

import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH     = "HIGH"
    MEDIUM   = "MEDIUM"
    LOW      = "LOW"
    INFO     = "INFO"


@dataclass
class Alert:
    """Representa um alerta gerado por um serviço."""
    id: str
    service: str
    severity: Severity
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    root_cause: Optional[str] = None  # Se conhecido, indica a causa raiz

    def __str__(self) -> str:
        root = f" [root: {self.root_cause}]" if self.root_cause else ""
        return (
            f"[{self.timestamp.strftime('%H:%M:%S')}] "
            f"[{self.severity.value}] "
            f"{self.service}: {self.message}{root}"
        )


# ---------------------------------------------------------------------------
# Topologia de serviços — dependências simples de microsserviços
# ---------------------------------------------------------------------------

SERVICE_DEPENDENCIES: dict[str, list[str]] = {
    "database":       [],                                    # sem dependências
    "cache":          ["database"],
    "auth-service":   ["database", "cache"],
    "user-service":   ["auth-service", "database"],
    "product-service":["database", "cache"],
    "cart-service":   ["user-service", "product-service"],
    "payment-service":["user-service", "cart-service"],
    "api-gateway":    ["auth-service", "user-service", "cart-service"],
    "frontend":       ["api-gateway"],
}

ALERT_TEMPLATES = {
    "database":        ("Connection timeout", Severity.CRITICAL),
    "cache":           ("Cache miss rate > 90%", Severity.HIGH),
    "auth-service":    ("Authentication failures spike", Severity.HIGH),
    "user-service":    ("User endpoint 5xx errors", Severity.HIGH),
    "product-service": ("Product catalog unavailable", Severity.MEDIUM),
    "cart-service":    ("Cart operations failing", Severity.HIGH),
    "payment-service": ("Payment processing errors", Severity.CRITICAL),
    "api-gateway":     ("Gateway upstream errors", Severity.HIGH),
    "frontend":        ("Frontend returning 503", Severity.CRITICAL),
}


def simulate_alert_storm(root_failure: str) -> list[Alert]:
    """
    Simula a propagação de uma falha em cascata a partir de um serviço raiz.

    Returns:
        Lista de alertas gerados em ordem cronológica (com delay simulado).
    """
    alerts: list[Alert] = []
    affected: set[str] = set()
    queue: list[str] = [root_failure]

    print("\n" + "=" * 60)
    print(f"💥 FALHA INICIADA: {root_failure}")
    print("=" * 60)

    while queue:
        service = queue.pop(0)
        if service in affected:
            continue
        affected.add(service)

        msg, severity = ALERT_TEMPLATES.get(service, ("Unknown error", Severity.MEDIUM))
        alert = Alert(
            id=f"ALT-{len(alerts)+1:04d}",
            service=service,
            severity=severity,
            message=msg,
            root_cause=root_failure if service != root_failure else None,
        )
        alerts.append(alert)
        print(f"  📢 {alert}")
        time.sleep(0.1)  # Simula o delay de propagação

        # Propaga para serviços que dependem deste
        for svc, deps in SERVICE_DEPENDENCIES.items():
            if service in deps and svc not in affected:
                queue.append(svc)

    return alerts


def analyze_alert_storm(alerts: list[Alert]) -> None:
    """
    Analisa o storm e exibe um resumo operacional.
    Demonstra o conceito básico de grouping e deduplicação.
    """
    print("\n" + "=" * 60)
    print("📊 ANÁLISE DO ALERT STORM")
    print("=" * 60)

    total = len(alerts)
    root_alerts = [a for a in alerts if a.root_cause is None]
    secondary_alerts = [a for a in alerts if a.root_cause is not None]

    severity_counts: dict[str, int] = {}
    for alert in alerts:
        severity_counts[alert.severity.value] = severity_counts.get(alert.severity.value, 0) + 1

    print(f"\n  Total de alertas gerados : {total}")
    print(f"  Alertas de causa raiz    : {len(root_alerts)}")
    print(f"  Alertas secundários      : {len(secondary_alerts)} ({len(secondary_alerts)/total*100:.0f}% de ruído)")

    print("\n  Distribuição por severidade:")
    for sev, count in sorted(severity_counts.items()):
        bar = "█" * count
        print(f"    {sev:<10} {bar} ({count})")

    if root_alerts:
        print(f"\n  🎯 Causa raiz identificável: {root_alerts[0].service}")
        print(f"     → Ao resolver '{root_alerts[0].service}', {len(secondary_alerts)} alertas seriam suprimidos.")

    noise_reduction = len(secondary_alerts) / total * 100
    print(f"\n  💡 Redução de ruído potencial: {noise_reduction:.0f}%")
    print("     (com correlação automatizada de eventos)")


if __name__ == "__main__":
    print("🔬 Demo: Alert Storm em Arquitetura de Microsserviços")
    print("     Nível 1 — AIOps & Automação de Incidentes")

    # Simula falha no banco de dados — o pior cenário
    failure_point = "database"
    alerts = simulate_alert_storm(root_failure=failure_point)
    analyze_alert_storm(alerts)

    print("\n" + "=" * 60)
    print("📌 CONCLUSÃO")
    print("=" * 60)
    print("""
  Sem correlação automatizada, o time de operações recebe TODOS
  esses alertas simultaneamente, tornando quase impossível
  identificar a causa raiz rapidamente.

  Na Aula 1.2, veremos como plataformas de AIOps correlacionam
  esses sinais automaticamente para reduzir o ruído operacional.
    """)
