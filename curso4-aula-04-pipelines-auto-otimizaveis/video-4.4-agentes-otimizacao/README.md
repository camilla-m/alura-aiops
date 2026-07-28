# Vídeo 4.4 — Agentes que otimizam o próprio pipeline

## 🎬 Roteiro

**Tipo:** Apresentar Teoria  
**Habilidade:** Construir um agente heurístico que analisa execuções passadas e propõe otimizações priorizadas por impacto.

### Desenvolvimento

1. **Cenário real:** Ninguém tem tempo de auditar o pipeline manualmente toda semana
2. **Teoria:** Raciocínio explicável passo a passo, sem depender de um LLM real

---

## 💡 Conceitos-chave

- **Heurísticas explicáveis:** Cada recomendação tem um "porquê" auditável
- **Impacto estimado:** Priorizar por minutos economizados, não por palpite
- **Tipos de melhoria:** Paralelizar, cachear, juntar/mover stage, quarentenar flaky
- **Human-in-the-loop:** O agente propõe; a mudança só entra com aprovação humana

---

## 📂 Arquivos deste vídeo

```
video-4.4-agentes-otimizacao/
├── README.md            ← Este arquivo
└── pipeline_agent.py    ← Agente heurístico de recomendações priorizadas
```

## ▶️ Como executar

```bash
python3 curso4-aula-04-pipelines-auto-otimizaveis/video-4.4-agentes-otimizacao/pipeline_agent.py
```
