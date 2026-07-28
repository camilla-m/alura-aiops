# Aula 4 — Pipelines auto-otimizáveis

## 🎯 Objetivo de aprendizagem

Identificar gargalos em pipelines de CI/CD e usar IA para aplicar paralelismo dinâmico, cache inteligente, skip seguro de stages e agentes que otimizam o próprio pipeline com recomendações explicáveis.

---

## 📹 Vídeos

| Vídeo | Título | Tipo |
|-------|--------|------|
| 4.1 | Identificando gargalos no pipeline | Contexto |
| 4.2 | Paralelismo dinâmico e cache inteligente | Solução |
| 4.3 | Skip seguro de stages por análise de diff | Solução |
| 4.4 | Agentes que otimizam o próprio pipeline | Teoria |
| 4.5 | Hands-on: Otimizando um pipeline de ponta a ponta | Prática |

---

## 🏗️ Estrutura

```
curso4-aula-04-pipelines-auto-otimizaveis/
├── README.md                          ← Este arquivo
├── video-4.1-gargalos-pipeline/       ← Contexto: Onde o tempo é gasto
├── video-4.2-paralelismo-cache/       ← Solução: DAG, paralelismo e cache
├── video-4.3-skip-stages/             ← Solução: Execução condicional segura
├── video-4.4-agentes-otimizacao/      ← Teoria: Agente de recomendações
└── video-4.5-hands-on/                ← Prática: Otimização before/after
```

---

## 🧩 Habilidades desenvolvidas

- Analisar histórico de execuções para localizar o stage gargalo e o caminho crítico
- Modelar dependências entre stages como um DAG e calcular o paralelismo ótimo
- Aplicar cache inteligente baseado em detecção de mudanças nos inputs
- Decidir com segurança quais stages podem ser pulados a partir do diff de mudanças
- Construir um agente heurístico que propõe otimizações priorizadas por impacto
- Medir o ganho real de um pipeline comparando cenários before/after
