"""
Vídeo 3.2 — Análise de logs e eventos operacionais com IA
==========================================================
Demonstra como enviar grandes volumes de logs para um LLM
e extrair padrões de falha de forma estruturada.

Conceitos demonstrados:
- Técnicas de chunking de logs para contornar limites de contexto
- Formulação de prompts para extração de stack traces
- Sumarização progressiva (map-reduce sobre logs)
- Padrões de extração: erros, warnings, anomalias
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class LogChunk:
    """Chunk de logs para envio ao LLM."""
    chunk_id: int
    lines: list[str]
    start_time: Optional[str] = None
    end_time: Optional[str] = None

    @property
    def text(self) -> str:
        return "\n".join(self.lines)

    @property
    def size(self) -> int:
        return len(self.text)


@dataclass
class LogPattern:
    """Padrão de log extraído pela análise."""
    pattern_type: str   # ERROR | EXCEPTION | TIMEOUT | etc.
    frequency: int
    first_seen: str
    last_seen: str
    sample: str
    components: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Gerador de logs simulados (incidente real)
# ---------------------------------------------------------------------------

SAMPLE_LOGS = """
2024-06-03 09:00:01 INFO  auth-service: Starting auth-service v2.3.1
2024-06-03 09:00:05 INFO  auth-service: Database connection pool initialized (max=100)
2024-06-03 09:01:12 INFO  auth-service: Token validated for user_id=7823
2024-06-03 09:01:45 INFO  auth-service: Token validated for user_id=4401
2024-06-03 09:02:03 WARN  auth-service: Connection pool at 80% capacity (80/100)
2024-06-03 09:02:07 ERROR auth-service: pq: too many connections
                          at db.Pool.Acquire (pool.go:147)
                          at auth.ValidateToken (auth.go:89)
                          at handlers.AuthMiddleware (middleware.go:34)
2024-06-03 09:02:08 ERROR auth-service: pq: too many connections
                          at db.Pool.Acquire (pool.go:147)
                          at auth.ValidateToken (auth.go:89)
2024-06-03 09:02:10 ERROR auth-service: pq: too many connections
                          at db.Pool.Acquire (pool.go:147)
2024-06-03 09:02:15 ERROR auth-service: context deadline exceeded after 30s
                          at db.Pool.Acquire (pool.go:147)
                          at auth.ValidateToken (auth.go:89)
2024-06-03 09:02:20 ERROR api-gateway: upstream auth-service: connection refused
                          at upstream.Forward (upstream.go:201)
                          at gateway.Route (router.go:88)
2024-06-03 09:02:25 ERROR api-gateway: upstream auth-service: connection refused
2024-06-03 09:02:30 WARN  frontend: auth-service unavailable, returning 503
2024-06-03 09:02:35 ERROR frontend: 503 Service Unavailable to 412 clients
2024-06-03 09:02:40 ERROR auth-service: pq: too many connections
2024-06-03 09:02:45 ERROR auth-service: pq: too many connections
2024-06-03 09:02:50 CRIT  auth-service: Connection pool exhausted (100/100), rejecting requests
                          at db.Pool.Acquire (pool.go:152)
2024-06-03 09:03:00 ERROR payment-service: auth-service health check failed
                          retrying in 5s...
2024-06-03 09:03:05 ERROR payment-service: auth-service health check failed (attempt 2/3)
2024-06-03 09:03:10 ERROR payment-service: auth-service health check failed (attempt 3/3)
                          marking auth-service as unhealthy
""".strip().splitlines()


# ---------------------------------------------------------------------------
# Utilitários de processamento de logs
# ---------------------------------------------------------------------------

def chunk_logs(
    logs: list[str],
    max_chars_per_chunk: int = 4000,
) -> list[LogChunk]:
    """
    Divide logs em chunks para contornar limites de contexto do LLM.
    Estratégia: chunk por tamanho, mantendo linhas inteiras.
    """
    chunks: list[LogChunk] = []
    current_lines: list[str] = []
    current_size = 0
    chunk_id = 0

    for line in logs:
        line_size = len(line) + 1
        if current_size + line_size > max_chars_per_chunk and current_lines:
            chunks.append(LogChunk(
                chunk_id=chunk_id,
                lines=current_lines,
                start_time=_extract_time(current_lines[0]),
                end_time=_extract_time(current_lines[-1]),
            ))
            chunk_id += 1
            current_lines = []
            current_size = 0

        current_lines.append(line)
        current_size += line_size

    if current_lines:
        chunks.append(LogChunk(
            chunk_id=chunk_id,
            lines=current_lines,
            start_time=_extract_time(current_lines[0]),
            end_time=_extract_time(current_lines[-1]),
        ))

    return chunks


def _extract_time(line: str) -> Optional[str]:
    match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
    return match.group(1) if match else None


def extract_patterns_local(logs: list[str]) -> list[LogPattern]:
    """
    Extração de padrões sem IA (regex-based) — para demonstrar o contraste
    com a abordagem assistida por LLM.
    """
    patterns: dict[str, LogPattern] = {}

    for line in logs:
        if "ERROR" in line or "CRIT" in line or "WARN" in line:
            # Extrai o tipo de erro
            if "too many connections" in line:
                key = "too_many_connections"
                ptype = "RESOURCE_EXHAUSTION"
            elif "connection refused" in line:
                key = "connection_refused"
                ptype = "CONNECTIVITY"
            elif "deadline exceeded" in line:
                key = "deadline_exceeded"
                ptype = "TIMEOUT"
            elif "health check failed" in line:
                key = "health_check_failed"
                ptype = "HEALTH"
            elif "503" in line:
                key = "http_503"
                ptype = "HTTP_ERROR"
            else:
                continue

            ts = _extract_time(line) or "unknown"
            service = line.split()[3].rstrip(":") if len(line.split()) > 3 else "unknown"

            if key not in patterns:
                patterns[key] = LogPattern(
                    pattern_type=ptype,
                    frequency=1,
                    first_seen=ts,
                    last_seen=ts,
                    sample=line[:100],
                    components=[service],
                )
            else:
                patterns[key].frequency += 1
                patterns[key].last_seen = ts
                if service not in patterns[key].components:
                    patterns[key].components.append(service)

    return sorted(patterns.values(), key=lambda p: p.frequency, reverse=True)


def build_log_analysis_prompt(chunk: LogChunk, service: str) -> str:
    """Prompt otimizado para análise de chunk de logs."""
    return f"""Você é um SRE sênior analisando logs de produção durante um incidente.

SERVIÇO: {service}
PERÍODO: {chunk.start_time} → {chunk.end_time}
TOTAL DE LINHAS: {len(chunk.lines)}

LOGS:
=====
{chunk.text}

ANÁLISE REQUERIDA:
==================
1. **Erro dominante**: qual mensagem de erro aparece com maior frequência?
2. **Timeline de degradação**: quando exatamente começou a falha?
3. **Stack traces relevantes**: quais módulos aparecem no caminho do erro?
4. **Causa raiz provável**: com base apenas nesses logs, qual a hipótese mais forte?
5. **Próxima investigação**: que informação adicional você precisaria para confirmar?

Seja objetivo. Cite linhas específicas para fundamentar suas conclusões.
"""


def demo_log_analysis() -> None:
    print("=" * 65)
    print("🔍 Demo: Análise de Logs com IA")
    print("   Nível 1 — AIOps & Automação de Incidentes")
    print("=" * 65)

    # PASSO 1: Extração tradicional (regex)
    print("\n" + "─" * 65)
    print("MÉTODO 1 — Extração por regex (sem IA)")
    print("─" * 65)
    patterns = extract_patterns_local(SAMPLE_LOGS)
    print(f"\n  {len(SAMPLE_LOGS)} linhas de log analisadas")
    print(f"  {len(patterns)} padrões extraídos:\n")
    for p in patterns:
        comps = ", ".join(p.components)
        print(f"  [{p.pattern_type:<22}] x{p.frequency:>3}  Serviços: {comps}")
        print(f"    {p.sample[:70]}")
        print()

    # PASSO 2: Chunking + prompt para LLM
    print("─" * 65)
    print("MÉTODO 2 — Análise via LLM (chunking + prompt)")
    print("─" * 65)
    chunks = chunk_logs(SAMPLE_LOGS, max_chars_per_chunk=4000)
    print(f"\n  Logs divididos em {len(chunks)} chunk(s)")

    for chunk in chunks:
        prompt = build_log_analysis_prompt(chunk, "auth-service/api-gateway")
        print(f"\n  📤 Chunk {chunk.chunk_id}: {len(chunk.lines)} linhas ({chunk.size} chars)")
        print(f"  ─────────────────────────────────────────")
        print(f"  PROMPT GERADO:")
        print()
        # Mostra apenas as primeiras 20 linhas do prompt para brevidade
        for line in prompt.splitlines()[:25]:
            print(f"  {line}")
        print(f"  ... [prompt completo enviado ao LLM]")

    print("\n" + "─" * 65)
    print("🆚 COMPARAÇÃO DOS MÉTODOS")
    print("─" * 65)
    print("""
  REGEX (tradicional):
  ✅ Rápido e sem custo de API
  ✅ Determinístico e auditável
  ❌ Não entende contexto ou causalidade
  ❌ Não extrai insights de stack traces complexas

  LLM (assistido por IA):
  ✅ Entende contexto e causalidade
  ✅ Extrai insights de stack traces em qualquer linguagem
  ✅ Gera hipóteses ranqueadas
  ❌ Custo de API e latência
  ❌ Pode alucinar — sempre validar com dados reais

  💡 RECOMENDAÇÃO: use regex para triagem inicial (barato/rápido)
     e LLM para análise aprofundada dos chunks mais relevantes.
    """)


if __name__ == "__main__":
    demo_log_analysis()
