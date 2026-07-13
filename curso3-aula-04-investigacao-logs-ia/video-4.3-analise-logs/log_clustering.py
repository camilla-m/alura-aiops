"""
Vídeo 4.3 — Análise inteligente de logs operacionais
======================================================
Demonstra agrupamento automático de logs para isolar exceções
e anomalias rapidamente em milhões de linhas de texto.

Conceitos demonstrados:
- Log pattern extraction (template mining)
- Agrupamento por similaridade de mensagens
- Detecção de clusters raros (anomalias)
- Redução de volume: milhões de linhas → poucos padrões
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class LogEntry:
    timestamp: datetime
    level: str
    service: str
    message: str
    raw: str = ""


@dataclass
class LogCluster:
    pattern: str
    count: int
    level: str
    services: list[str]
    sample: str
    first_seen: datetime
    last_seen: datetime
    is_anomaly: bool = False


def tokenize_log(message: str) -> str:
    """
    Extrai template de uma mensagem de log substituindo
    valores dinâmicos por placeholders.
    """
    # Substituir IPs
    pattern = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '<IP>', message)
    # Substituir UUIDs
    pattern = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '<UUID>', pattern)
    # Substituir números
    pattern = re.sub(r'=\d+(\.\d+)?', '=<NUM>', pattern)
    pattern = re.sub(r'\b\d{4,}\b', '<NUM>', pattern)
    # Substituir timestamps
    pattern = re.sub(r'\d{2}:\d{2}:\d{2}', '<TIME>', pattern)
    # Substituir paths
    pattern = re.sub(r'/[a-zA-Z0-9/_\-\.]+', '<PATH>', pattern)
    return pattern


def generate_log_data() -> list[LogEntry]:
    """Gera logs realistas com padrões normais e anomalias."""
    base = datetime(2024, 8, 20, 14, 0, 0)
    logs = []

    # Padrão 1: Request logs normais (alto volume)
    for i in range(200):
        ts = base + timedelta(seconds=i * 0.5)
        ip = f"192.168.1.{(i % 50) + 10}"
        path = ["/api/users", "/api/products", "/api/cart", "/api/health"][i % 4]
        status = 200 if i % 20 != 0 else 304
        duration = 45 + (hash(str(i)) % 80)
        logs.append(LogEntry(ts, "INFO", "api-gateway",
            f"GET {path} from {ip} — {status} in {duration}ms"))

    # Padrão 2: Auth logs normais
    for i in range(80):
        ts = base + timedelta(seconds=i * 1.2)
        uid = f"usr-{1000 + i}"
        logs.append(LogEntry(ts, "INFO", "auth-service",
            f"Authentication successful for user {uid}"))

    # Padrão 3: Cache hits/misses normais
    for i in range(60):
        ts = base + timedelta(seconds=i * 1.5)
        key = f"product:{2000 + i}"
        hit = "HIT" if i % 3 != 0 else "MISS"
        logs.append(LogEntry(ts, "DEBUG", "cache",
            f"Cache {hit} for key {key} (ttl=300s)"))

    # ANOMALIA 1: NullPointerException (rara — bug no código)
    for i in range(5):
        ts = base + timedelta(minutes=2, seconds=i * 10)
        logs.append(LogEntry(ts, "ERROR", "checkout-service",
            f"java.lang.NullPointerException at CheckoutHandler.processPayment"
            f"(CheckoutHandler.java:142) — cart_id=cart-{8000 + i}"))

    # ANOMALIA 2: Connection timeout (rara — infra)
    for i in range(8):
        ts = base + timedelta(minutes=3, seconds=i * 8)
        logs.append(LogEntry(ts, "ERROR", "user-service",
            f"Connection timeout after 30000ms connecting to postgres-primary"
            f":5432 — pool_active=98/100"))

    # ANOMALIA 3: Uma única ocorrência (muito rara)
    logs.append(LogEntry(base + timedelta(minutes=4), "FATAL", "payment-service",
        "FATAL: Unexpected state transition PENDING->REFUNDED without "
        "intermediate COMPLETED state — transaction_id=txn-99999"))

    # Padrão 4: Cron jobs normais
    for i in range(10):
        ts = base + timedelta(minutes=5 * i)
        logs.append(LogEntry(ts, "INFO", "scheduler",
            f"Cron job 'cleanup-expired-sessions' completed in {120 + i * 5}ms"))

    return logs


def cluster_logs(logs: list[LogEntry]) -> list[LogCluster]:
    """Agrupa logs por pattern extraído."""
    pattern_map: dict[str, list[LogEntry]] = {}

    for log in logs:
        pattern = tokenize_log(log.message)
        pattern_map.setdefault(pattern, []).append(log)

    clusters = []
    total_logs = len(logs)

    for pattern, entries in pattern_map.items():
        count = len(entries)
        services = list(set(e.service for e in entries))
        levels = Counter(e.level for e in entries)
        dominant_level = levels.most_common(1)[0][0]

        timestamps = [e.timestamp for e in entries]

        # Anomalia: cluster raro com nível ERROR/FATAL
        is_anomaly = (
            count < total_logs * 0.02  # Menos de 2% do total
            and dominant_level in ("ERROR", "FATAL")
        )

        clusters.append(LogCluster(
            pattern=pattern,
            count=count,
            level=dominant_level,
            services=services,
            sample=entries[0].message,
            first_seen=min(timestamps),
            last_seen=max(timestamps),
            is_anomaly=is_anomaly,
        ))

    return sorted(clusters, key=lambda c: c.count, reverse=True)


def run_demo() -> None:
    print("=" * 70)
    print("📋 Demo: Análise Inteligente de Logs Operacionais")
    print("   Curso 3 — Observabilidade Inteligente")
    print("=" * 70)

    logs = generate_log_data()
    print(f"\n  📥 {len(logs)} linhas de log recebidas")
    print(f"  ⏰ Período: {logs[0].timestamp.strftime('%H:%M')} — {logs[-1].timestamp.strftime('%H:%M')}")

    # Antes: visão bruta
    print(f"\n{'─' * 70}")
    print("📝 ANTES: Visão bruta (primeiras 10 linhas)")
    print(f"{'─' * 70}")
    for log in logs[:10]:
        print(f"  [{log.timestamp.strftime('%H:%M:%S')}] [{log.level:5}] {log.service}: {log.message[:65]}...")

    print(f"\n  ⚠️  Vasculhar {len(logs)} linhas manualmente é impraticável!")

    # Depois: clusters
    print(f"\n{'─' * 70}")
    print("📊 DEPOIS: Logs agrupados por padrão")
    print(f"{'─' * 70}")

    clusters = cluster_logs(logs)

    print(f"\n  {len(logs)} linhas → {len(clusters)} padrões únicos "
          f"(redução de {(1 - len(clusters) / len(logs)) * 100:.0f}%)\n")

    for i, c in enumerate(clusters):
        anomaly_tag = " 🚨 ANOMALIA" if c.is_anomaly else ""
        pct = c.count / len(logs) * 100
        bar = "█" * max(1, int(pct / 2))

        print(f"  Padrão #{i + 1} [{c.level:5}] ({c.count:>4}x, {pct:>5.1f}%) {bar}{anomaly_tag}")
        print(f"    Serviços: {', '.join(c.services)}")
        print(f"    Exemplo : {c.sample[:70]}...")
        print(f"    Template: {c.pattern[:70]}...")
        print()

    # Foco nas anomalias
    anomalies = [c for c in clusters if c.is_anomaly]
    print(f"{'─' * 70}")
    print(f"🚨 ANOMALIAS DETECTADAS ({len(anomalies)} padrões raros)")
    print(f"{'─' * 70}")

    for c in anomalies:
        print(f"\n  ❌ [{c.level}] {c.count}x ocorrências em {', '.join(c.services)}")
        print(f"     Primeira: {c.first_seen.strftime('%H:%M:%S')}")
        print(f"     Última  : {c.last_seen.strftime('%H:%M:%S')}")
        print(f"     Exemplo : {c.sample}")

    print("\n" + "=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print(f"""
  O agrupamento automático de logs reduziu {len(logs)} linhas para
  {len(clusters)} padrões, e destacou {len(anomalies)} anomalias que
  precisam de investigação imediata.

  Em produção, ferramentas como Datadog Log Patterns, Elastic ML,
  e Loki LogQL fazem isso em tempo real com milhões de linhas/min.

  Na Aula 4.4, veremos como detectar anomalias SEQUENCIAIS —
  quebras na ordem esperada de eventos em logs.
    """)


if __name__ == "__main__":
    run_demo()
