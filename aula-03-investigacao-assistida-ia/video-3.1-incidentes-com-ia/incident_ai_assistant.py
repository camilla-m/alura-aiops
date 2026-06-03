"""
Vídeo 3.1 — Investigando incidentes com apoio de IA
====================================================
Demonstra como usar LLMs para acelerar o diagnóstico
inicial de um incidente crítico.

Conceitos demonstrados:
- Formulação de prompts eficazes para diagnóstico de incidentes
- Estruturação do contexto do incidente para a IA
- Iteração de prompts para refinamento do diagnóstico
- Limitações e boas práticas de uso de LLMs em operações
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

# Requer: pip install openai python-dotenv
# Configure OPENAI_API_KEY no arquivo .env


@dataclass
class IncidentContext:
    """Contexto estruturado de um incidente para enviar à IA."""
    title: str
    started_at: str
    affected_services: list[str]
    symptoms: list[str]
    recent_changes: list[str]
    error_samples: list[str]
    metrics_snapshot: dict[str, str]


def build_incident_prompt(ctx: IncidentContext) -> str:
    """
    Constrói um prompt estruturado para diagnóstico de incidente.

    Princípios de prompt engineering para operações:
    1. Contexto específico e detalhado
    2. Formato de saída esperado definido
    3. Restrições claras (não inventar fatos)
    4. Pedido de hipóteses ranqueadas por probabilidade
    """
    symptoms_text    = "\n".join(f"  - {s}" for s in ctx.symptoms)
    changes_text     = "\n".join(f"  - {c}" for c in ctx.recent_changes)
    errors_text      = "\n".join(f"  - {e}" for e in ctx.error_samples)
    services_text    = ", ".join(ctx.affected_services)
    metrics_text     = "\n".join(f"  - {k}: {v}" for k, v in ctx.metrics_snapshot.items())

    return f"""Você é um SRE sênior especialista em sistemas distribuídos e observabilidade.

INCIDENTE EM ANDAMENTO
======================
Título      : {ctx.title}
Início      : {ctx.started_at}
Serviços    : {services_text}

SINTOMAS OBSERVADOS
===================
{symptoms_text}

MUDANÇAS RECENTES (últimas 24h)
================================
{changes_text}

AMOSTRAS DE ERROS (últimas 15 min)
====================================
{errors_text}

MÉTRICAS ATUAIS
================
{metrics_text}

TAREFA
======
Com base no contexto acima, realize a seguinte análise:

1. **Hipóteses de causa raiz** (liste as 3 mais prováveis, ordenadas por probabilidade)
   Para cada hipótese, explique:
   - Por que é uma hipótese válida dado o contexto
   - Como confirmar ou descartar em menos de 5 minutos

2. **Ações imediatas** (próximos 10 minutos)
   - O que fazer AGORA para limitar o impacto

3. **Investigação aprofundada** (se as ações imediatas não resolverem)
   - Quais dados adicionais coletar
   - Quais comandos/queries executar

4. **Sinais de melhora**
   - Como saber que o incidente está se resolvendo

IMPORTANTE: Baseie-se SOMENTE nos dados fornecidos. Se precisar de informações
adicionais para confirmar uma hipótese, liste-as explicitamente.
"""


def build_log_analysis_prompt(logs: list[str], service: str) -> str:
    """
    Prompt específico para análise de grande volume de logs.
    Demonstra a técnica de sumarização estruturada.
    """
    logs_text = "\n".join(logs)
    return f"""Analise os seguintes logs do serviço '{service}' e extraia:

LOGS (últimos 100 registros)
=============================
{logs_text}

EXTRAIA as seguintes informações:
1. **Padrão de erro dominante**: qual erro aparece com mais frequência?
2. **Timeline**: quando exatamente os erros começaram?
3. **Componentes afetados**: quais módulos/dependências aparecem nas stack traces?
4. **Anomalias**: há algo incomum que destoa do padrão de erro principal?
5. **Próximos passos de investigação**: baseado nos logs, o que verificar a seguir?

Responda de forma objetiva e estruturada. Cite trechos específicos dos logs.
"""


# ---------------------------------------------------------------------------
# Demo sem API (modo simulado para uso em aula)
# ---------------------------------------------------------------------------

SIMULATED_INCIDENT = IncidentContext(
    title="Frontend retornando 503 para 40% dos usuários",
    started_at="2024-06-03 09:02 UTC",
    affected_services=["frontend", "api-gateway", "auth-service"],
    symptoms=[
        "Taxa de erro HTTP 503 em 42% das requisições ao frontend",
        "Latência p99 do api-gateway: 12.000ms (normal: 250ms)",
        "auth-service health check falhando intermitentemente",
        "Connection pool do PostgreSQL em 98% de utilização",
    ],
    recent_changes=[
        "Deploy do auth-service v2.3.1 às 08:45 UTC (15 min antes do incidente)",
        "Migração de schema do banco de sessões às 08:30 UTC",
        "Nenhuma mudança de configuração de infraestrutura",
    ],
    error_samples=[
        "[09:02:15] auth-service ERROR: pq: too many connections (max=100)",
        "[09:02:17] auth-service ERROR: context deadline exceeded after 30s",
        "[09:02:20] api-gateway ERROR: upstream auth-service: connection refused",
        "[09:03:01] frontend WARN: 503 Service Unavailable — auth-service unreachable",
    ],
    metrics_snapshot={
        "postgresql.connections.active": "98/100",
        "auth-service.error_rate":       "0.89 (89%)",
        "api-gateway.latency_p99":       "12.000ms",
        "frontend.http_5xx_rate":        "0.42 (42%)",
    },
)


def demo_without_api() -> None:
    """Demonstra a estrutura dos prompts sem chamar a API."""
    print("=" * 65)
    print("🤖 Demo: Investigação de Incidentes com Apoio de IA")
    print("   Nível 1 — AIOps & Automação de Incidentes")
    print("=" * 65)

    print("\n📋 CONTEXTO DO INCIDENTE:")
    print(f"   {SIMULATED_INCIDENT.title}")
    print(f"   Início: {SIMULATED_INCIDENT.started_at}")

    print("\n" + "─" * 65)
    print("PROMPT GERADO PARA O LLM (Diagnóstico de Incidente):")
    print("─" * 65)
    prompt = build_incident_prompt(SIMULATED_INCIDENT)
    print(prompt)

    print("\n" + "─" * 65)
    print("💡 USANDO A API (requer OPENAI_API_KEY no .env):")
    print("─" * 65)
    print("""
  from openai import OpenAI
  import os

  client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

  response = client.chat.completions.create(
      model="gpt-4o",
      messages=[
          {"role": "system", "content": "Você é um SRE sênior especialista em AIOps."},
          {"role": "user",   "content": prompt},
      ],
      temperature=0.1,  # baixo para respostas mais determinísticas
  )
  print(response.choices[0].message.content)
    """)

    print("\n" + "─" * 65)
    print("📝 BOAS PRÁTICAS DE PROMPT ENGINEERING PARA OPERAÇÕES:")
    print("─" * 65)
    print("""
  1. Defina o PAPEL da IA antes de qualquer instrução
     ("Você é um SRE sênior especialista em...")

  2. Forneça CONTEXTO ESTRUTURADO, não texto livre
     (use seções claras: sintomas, mudanças, erros, métricas)

  3. Peça HIPÓTESES RANQUEADAS, não uma única resposta
     ("liste as 3 causas mais prováveis, ordenadas por probabilidade")

  4. Exija CITAÇÕES DOS DADOS fornecidos
     ("Baseie-se SOMENTE nos dados fornecidos")

  5. Defina o FORMATO DE SAÍDA esperado
     (seções numeradas, bullet points, com/sem markdown)

  6. Use TEMPERATURA BAIXA para diagnósticos técnicos
     (temperature=0.1 para respostas mais determinísticas)
    """)


if __name__ == "__main__":
    demo_without_api()
