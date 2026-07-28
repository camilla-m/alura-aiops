# Vídeo 4.1 — Identificando gargalos no pipeline

## 🎬 Roteiro

**Tipo:** Apresentar Contexto  
**Habilidade:** Analisar o histórico de execuções de um pipeline para localizar o stage gargalo e o caminho crítico.

### Desenvolvimento

1. **Cenário real:** Um pipeline de 25+ minutos frustra o time e atrasa entregas
2. **Teoria:** Como medir a contribuição de cada stage e identificar variância suspeita

---

## 💡 Conceitos-chave

- **Caminho crítico:** A sequência de stages que determina o tempo total mínimo
- **Stage gargalo:** O stage com maior contribuição percentual no tempo total
- **Variância:** Stages instáveis (alto desvio-padrão) escondem flakiness e retries
- **Percentil p95:** Mede o pior caso realista, não só a média otimista

---

## 📂 Arquivos deste vídeo

```
video-4.1-gargalos-pipeline/
├── README.md                 ← Este arquivo
└── pipeline_bottlenecks.py   ← Análise de gargalos por histórico de runs
```

## ▶️ Como executar

```bash
python3 curso4-aula-04-pipelines-auto-otimizaveis/video-4.1-gargalos-pipeline/pipeline_bottlenecks.py
```
