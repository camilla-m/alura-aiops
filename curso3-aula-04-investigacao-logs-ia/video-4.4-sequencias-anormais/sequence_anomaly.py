"""
Vídeo 4.4 — Detectando sequências e comportamentos anormais
=============================================================
Demonstra detecção de quebras de sequência lógica em padrões
operacionais de logs que precedem indisponibilidades críticas.

Conceitos demonstrados:
- Sequência esperada de eventos (happy path)
- Detecção de steps faltantes ou fora de ordem
- Transições de estado ilegais
- Correlação entre quebras de sequência e incidentes
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class StepStatus(str, Enum):
    COMPLETED = "✅"
    MISSING   = "❌"
    OUT_ORDER = "⚠️"
    UNEXPECTED = "🔴"


@dataclass
class WorkflowStep:
    """Um passo em um workflow esperado."""
    name: str
    expected_order: int
    actual_order: int | None = None
    timestamp: datetime | None = None
    status: StepStatus = StepStatus.MISSING


@dataclass
class WorkflowInstance:
    """Uma instância de execução de um workflow."""
    workflow_id: str
    transaction_id: str
    steps: list[WorkflowStep]
    is_anomalous: bool = False
    anomaly_reason: str = ""


# ---------------------------------------------------------------------------
# Definição do workflow esperado de checkout
# ---------------------------------------------------------------------------

EXPECTED_CHECKOUT_SEQUENCE = [
    "cart.validate",
    "inventory.check",
    "user.authenticate",
    "payment.authorize",
    "payment.capture",
    "order.create",
    "notification.send",
    "analytics.track",
]

EXPECTED_DEPLOY_SEQUENCE = [
    "build.start",
    "build.test",
    "build.package",
    "deploy.canary",
    "deploy.health_check",
    "deploy.promote",
    "deploy.verify",
]


def generate_checkout_logs() -> list[dict]:
    """Gera logs de checkout com sequências normais e anômalas."""
    base = datetime(2024, 8, 20, 14, 0, 0)
    logs = []

    # Transação 1: Normal (happy path)
    txn1_base = base
    for i, step in enumerate(EXPECTED_CHECKOUT_SEQUENCE):
        logs.append({
            "txn_id": "txn-001", "step": step,
            "timestamp": txn1_base + timedelta(milliseconds=i * 200),
            "status": "OK",
        })

    # Transação 2: Normal
    txn2_base = base + timedelta(seconds=5)
    for i, step in enumerate(EXPECTED_CHECKOUT_SEQUENCE):
        logs.append({
            "txn_id": "txn-002", "step": step,
            "timestamp": txn2_base + timedelta(milliseconds=i * 180),
            "status": "OK",
        })

    # Transação 3: ANÔMALA — pula inventory.check
    txn3_base = base + timedelta(seconds=10)
    for i, step in enumerate(EXPECTED_CHECKOUT_SEQUENCE):
        if step == "inventory.check":
            continue  # Step faltante!
        logs.append({
            "txn_id": "txn-003", "step": step,
            "timestamp": txn3_base + timedelta(milliseconds=i * 200),
            "status": "OK",
        })

    # Transação 4: ANÔMALA — payment.capture antes de payment.authorize
    txn4_base = base + timedelta(seconds=15)
    swapped = EXPECTED_CHECKOUT_SEQUENCE.copy()
    idx_auth = swapped.index("payment.authorize")
    idx_cap = swapped.index("payment.capture")
    swapped[idx_auth], swapped[idx_cap] = swapped[idx_cap], swapped[idx_auth]
    for i, step in enumerate(swapped):
        logs.append({
            "txn_id": "txn-004", "step": step,
            "timestamp": txn4_base + timedelta(milliseconds=i * 200),
            "status": "OK",
        })

    # Transação 5: ANÔMALA — step inesperado (payment.refund sem order.create)
    txn5_base = base + timedelta(seconds=20)
    for step in ["cart.validate", "user.authenticate", "payment.authorize", "payment.refund"]:
        logs.append({
            "txn_id": "txn-005", "step": step,
            "timestamp": txn5_base + timedelta(milliseconds=EXPECTED_CHECKOUT_SEQUENCE.index(step) * 200 if step in EXPECTED_CHECKOUT_SEQUENCE else 999),
            "status": "OK" if step != "payment.refund" else "UNEXPECTED",
        })

    # Transação 6: Normal
    txn6_base = base + timedelta(seconds=25)
    for i, step in enumerate(EXPECTED_CHECKOUT_SEQUENCE):
        logs.append({
            "txn_id": "txn-006", "step": step,
            "timestamp": txn6_base + timedelta(milliseconds=i * 210),
            "status": "OK",
        })

    return logs


def analyze_sequence(
    txn_id: str,
    events: list[dict],
    expected: list[str],
) -> WorkflowInstance:
    """Analisa uma sequência de eventos contra o padrão esperado."""
    actual_steps = [e["step"] for e in sorted(events, key=lambda e: e["timestamp"])]

    workflow_steps: list[WorkflowStep] = []
    anomalies = []

    # Verificar cada step esperado
    for i, expected_step in enumerate(expected):
        if expected_step in actual_steps:
            actual_pos = actual_steps.index(expected_step)
            if actual_pos != i and actual_pos < len(actual_steps):
                # Fora de ordem
                ws = WorkflowStep(
                    name=expected_step, expected_order=i,
                    actual_order=actual_pos,
                    timestamp=events[actual_pos]["timestamp"] if actual_pos < len(events) else None,
                    status=StepStatus.OUT_ORDER,
                )
                anomalies.append(f"Step '{expected_step}' fora de ordem (esperado: #{i}, real: #{actual_pos})")
            else:
                ws = WorkflowStep(
                    name=expected_step, expected_order=i,
                    actual_order=actual_pos,
                    timestamp=events[min(actual_pos, len(events) - 1)]["timestamp"],
                    status=StepStatus.COMPLETED,
                )
        else:
            ws = WorkflowStep(
                name=expected_step, expected_order=i,
                status=StepStatus.MISSING,
            )
            anomalies.append(f"Step '{expected_step}' AUSENTE na sequência")

        workflow_steps.append(ws)

    # Verificar steps inesperados
    for step in actual_steps:
        if step not in expected:
            workflow_steps.append(WorkflowStep(
                name=step, expected_order=-1,
                status=StepStatus.UNEXPECTED,
            ))
            anomalies.append(f"Step INESPERADO: '{step}' não faz parte do workflow")

    is_anomalous = len(anomalies) > 0
    reason = "; ".join(anomalies) if anomalies else "Sequência OK"

    return WorkflowInstance(
        workflow_id="checkout",
        transaction_id=txn_id,
        steps=workflow_steps,
        is_anomalous=is_anomalous,
        anomaly_reason=reason,
    )


def run_demo() -> None:
    print("=" * 70)
    print("🔗 Demo: Detectando Sequências e Comportamentos Anormais")
    print("   Curso 3 — Observabilidade Inteligente")
    print("=" * 70)

    # Workflow esperado
    print(f"\n{'─' * 70}")
    print("📋 WORKFLOW ESPERADO: Checkout")
    print(f"{'─' * 70}")
    for i, step in enumerate(EXPECTED_CHECKOUT_SEQUENCE):
        print(f"  {i + 1}. {step}")

    # Gerar e analisar logs
    logs = generate_checkout_logs()

    # Agrupar por transação
    txn_groups: dict[str, list[dict]] = {}
    for log in logs:
        txn_groups.setdefault(log["txn_id"], []).append(log)

    print(f"\n{'─' * 70}")
    print(f"🔍 ANÁLISE DE {len(txn_groups)} TRANSAÇÕES")
    print(f"{'─' * 70}")

    results: list[WorkflowInstance] = []
    for txn_id in sorted(txn_groups.keys()):
        events = txn_groups[txn_id]
        result = analyze_sequence(txn_id, events, EXPECTED_CHECKOUT_SEQUENCE)
        results.append(result)

        icon = "🔴" if result.is_anomalous else "🟢"
        print(f"\n  {icon} Transação {txn_id}:")

        for step in result.steps:
            order_info = ""
            if step.status == StepStatus.OUT_ORDER:
                order_info = f" (esperado: #{step.expected_order}, real: #{step.actual_order})"
            elif step.status == StepStatus.UNEXPECTED:
                order_info = " (NÃO ESPERADO no workflow!)"
            print(f"    {step.status.value} {step.name}{order_info}")

        if result.is_anomalous:
            print(f"    ⚠️  {result.anomaly_reason}")

    # Resumo
    normal = sum(1 for r in results if not r.is_anomalous)
    anomalous = sum(1 for r in results if r.is_anomalous)

    print(f"\n{'=' * 70}")
    print("📊 RESUMO")
    print(f"{'=' * 70}")
    print(f"\n  Transações analisadas : {len(results)}")
    print(f"  Sequências normais   : {normal} ({normal / len(results) * 100:.0f}%)")
    print(f"  Sequências anômalas  : {anomalous} ({anomalous / len(results) * 100:.0f}%)")

    print(f"\n  Tipos de anomalias encontradas:")
    for r in results:
        if r.is_anomalous:
            print(f"    🔴 {r.transaction_id}: {r.anomaly_reason}")

    print(f"""
  💡 IMPORTÂNCIA DA ANÁLISE SEQUENCIAL:

  • Step faltante: Indica bypass de validação (risco de segurança)
  • Step fora de ordem: Bug de concorrência ou race condition
  • Step inesperado: Fluxo não previsto (possível exploração)

  Essas anomalias frequentemente PRECEDEM incidentes críticos.
  Detectá-las nos logs permite ação preventiva antes da falha.
    """)

    print("=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  A análise sequencial de logs complementa o clustering (4.3)
  ao verificar não apenas O QUE aconteceu, mas se aconteceu
  NA ORDEM CORRETA. Isso é fundamental para detectar:
  - Bugs de concorrência
  - Bypasses de segurança
  - State machine violations

  Na Aula 4.5 (Hands-on), vamos combinar todas essas técnicas
  em uma investigação completa com IA e logs.
    """)


if __name__ == "__main__":
    run_demo()
