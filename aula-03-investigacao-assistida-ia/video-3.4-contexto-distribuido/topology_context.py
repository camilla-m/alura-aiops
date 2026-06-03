"""
Vídeo 3.4 — Contexto operacional em ambientes distribuídos
===========================================================
Demonstra como os limites de contexto dos LLMs influenciam
a análise de topologias complexas de microsserviços e como
estruturar o input de dados de topologia para máxima eficácia.

Conceitos demonstrados:
- Context window limitations dos LLMs
- Estratégias de compressão de topologia para o prompt
- Serialização de grafos de dependência para LLMs
- Map-reduce para análise de ambientes muito grandes
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ServiceNode:
    """Nó de serviço no grafo de topologia."""
    name: str
    type: str           # web | api | db | cache | queue | external
    tier: int           # 1=crítico, 2=importante, 3=auxiliar
    language: str       # python | go | java | node
    version: str
    replicas: int
    dependencies: list[str] = field(default_factory=list)
    health: str = "healthy"  # healthy | degraded | down
    latency_p99_ms: float = 0.0
    error_rate: float = 0.0


# ---------------------------------------------------------------------------
# Grafo de topologia do sistema
# ---------------------------------------------------------------------------

TOPOLOGY: dict[str, ServiceNode] = {
    "postgresql-primary": ServiceNode(
        "postgresql-primary", "db", 1, "sql", "15.3",  2,
        health="degraded", latency_p99_ms=2800.0, error_rate=0.0,
    ),
    "redis-cluster": ServiceNode(
        "redis-cluster", "cache", 1, "c", "7.2", 3,
        dependencies=["postgresql-primary"],
        health="healthy", latency_p99_ms=2.0,
    ),
    "auth-service": ServiceNode(
        "auth-service", "api", 1, "go", "2.3.1", 3,
        dependencies=["postgresql-primary", "redis-cluster"],
        health="degraded", latency_p99_ms=8500.0, error_rate=0.89,
    ),
    "user-service": ServiceNode(
        "user-service", "api", 2, "python", "3.1.0", 2,
        dependencies=["auth-service", "postgresql-primary"],
        health="degraded", latency_p99_ms=9200.0, error_rate=0.45,
    ),
    "product-service": ServiceNode(
        "product-service", "api", 2, "java", "2.0.5", 3,
        dependencies=["postgresql-primary", "redis-cluster"],
        health="healthy", latency_p99_ms=120.0, error_rate=0.01,
    ),
    "cart-service": ServiceNode(
        "cart-service", "api", 2, "node", "1.5.2", 2,
        dependencies=["user-service", "product-service", "redis-cluster"],
        health="degraded", latency_p99_ms=9800.0, error_rate=0.38,
    ),
    "payment-service": ServiceNode(
        "payment-service", "api", 1, "java", "4.1.0", 2,
        dependencies=["auth-service", "cart-service"],
        health="down", latency_p99_ms=0.0, error_rate=1.0,
    ),
    "api-gateway": ServiceNode(
        "api-gateway", "web", 1, "go", "1.9.0", 3,
        dependencies=["auth-service", "user-service", "product-service"],
        health="degraded", latency_p99_ms=12000.0, error_rate=0.42,
    ),
    "frontend": ServiceNode(
        "frontend", "web", 1, "node", "2.2.0", 2,
        dependencies=["api-gateway"],
        health="degraded", latency_p99_ms=13500.0, error_rate=0.42,
    ),
    "notification-service": ServiceNode(
        "notification-service", "api", 3, "python", "1.2.0", 1,
        dependencies=["postgresql-primary", "redis-cluster"],
        health="healthy", latency_p99_ms=95.0, error_rate=0.00,
    ),
    "analytics-worker": ServiceNode(
        "analytics-worker", "queue", 3, "python", "1.8.0", 1,
        dependencies=["postgresql-primary"],
        health="healthy", latency_p99_ms=450.0, error_rate=0.02,
    ),
}


# ---------------------------------------------------------------------------
# Serialização de topologia para LLM
# ---------------------------------------------------------------------------

def topology_to_prompt_context(
    topology: dict[str, ServiceNode],
    focus_services: Optional[list[str]] = None,
    max_chars: int = 3000,
) -> str:
    """
    Serializa o grafo de topologia em formato compacto e estruturado
    para uso como contexto em prompts de LLM.

    Estratégias de compressão:
    - Foco nos serviços degradados primeiro
    - Formato tabular compacto (menos tokens)
    - Limita serviços saudáveis não-relacionados
    """
    lines = ["TOPOLOGIA DO SISTEMA (estado atual)\n"]
    lines.append(f"{'Serviço':<25} {'Tipo':<8} {'Saúde':<10} {'Erros':>7} {'P99':>8}  Dependências")
    lines.append("─" * 90)

    # Ordena: degradados/down primeiro
    health_order = {"down": 0, "degraded": 1, "healthy": 2}
    sorted_nodes = sorted(topology.values(), key=lambda n: health_order.get(n.health, 3))

    # Se há foco, mostra serviços focados primeiro
    if focus_services:
        focused = [n for n in sorted_nodes if n.name in focus_services]
        others  = [n for n in sorted_nodes if n.name not in focus_services]
        sorted_nodes = focused + others

    for node in sorted_nodes:
        health_icon = {"healthy": "✅", "degraded": "⚠️ ", "down": "🔴"}.get(node.health, "❓")
        deps = ", ".join(node.dependencies) if node.dependencies else "—"
        line = (
            f"{node.name:<25} {node.type:<8} {health_icon} {node.health:<8} "
            f"{node.error_rate:>6.0%} {node.latency_p99_ms:>7.0f}ms  {deps}"
        )
        lines.append(line)

    result = "\n".join(lines)

    # Trunca se necessário (context window limit)
    if len(result) > max_chars:
        result = result[:max_chars] + "\n... [topologia truncada — use foco em serviços específicos]"

    return result


def build_topology_prompt(
    topology: dict[str, ServiceNode],
    incident_description: str,
) -> str:
    """Prompt que incorpora a topologia como contexto estruturado."""
    degraded = [n.name for n in topology.values() if n.health != "healthy"]
    topology_ctx = topology_to_prompt_context(topology, focus_services=degraded)

    return f"""Você é um SRE especialista analisando um incidente em ambiente de microsserviços.

INCIDENTE:
{incident_description}

{topology_ctx}

Com base na topologia acima:
1. Quais serviços degradados/down são candidatos a causa raiz?
   (considere: qual serviço causa mais impacto downstream ao falhar?)
2. Qual o "caminho crítico" da falha até o usuário final?
3. Há serviços saudáveis que confirmam ou descartam hipóteses?
4. Recomende a ordem de investigação (do mais provável ao menos provável).
"""


def print_topology_report(topology: dict[str, ServiceNode]) -> None:
    print("\n" + "=" * 65)
    print("🗺️  MAPA DE TOPOLOGIA — ESTADO ATUAL")
    print("=" * 65)

    healthy = [n for n in topology.values() if n.health == "healthy"]
    degraded = [n for n in topology.values() if n.health == "degraded"]
    down = [n for n in topology.values() if n.health == "down"]

    print(f"\n  ✅ Saudáveis  : {len(healthy)} serviços")
    print(f"  ⚠️  Degradados : {len(degraded)} serviços → {[n.name for n in degraded]}")
    print(f"  🔴 Indisponíveis: {len(down)} serviços → {[n.name for n in down]}")

    print(f"\n  Contexto serializado para LLM:\n")
    ctx = topology_to_prompt_context(topology)
    for line in ctx.splitlines():
        print(f"  {line}")

    print(f"\n  Tamanho do contexto: {len(ctx)} chars")
    print(f"  (Tokens estimados: ~{len(ctx)//4})")


if __name__ == "__main__":
    print("🔬 Demo: Contexto Operacional em Ambientes Distribuídos")
    print("     Nível 1 — AIOps & Automação de Incidentes")

    print_topology_report(TOPOLOGY)

    incident = "Frontend retornando 503 para 42% dos usuários desde 09:02 UTC. auth-service com 89% de taxa de erro."
    prompt = build_topology_prompt(TOPOLOGY, incident)

    print("\n" + "─" * 65)
    print("PROMPT COMPLETO GERADO:")
    print("─" * 65)
    print(prompt)
