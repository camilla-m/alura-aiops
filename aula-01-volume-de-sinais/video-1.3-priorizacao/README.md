# Vídeo 1.3 — Priorização operacional baseada em contexto

## 🎬 Roteiro

**Tipo:** Demonstrar Solução  
**Habilidade:** Avaliar o impacto real de falhas no ecossistema de infraestrutura para triagem eficiente.

### Desenvolvimento

- **Solução:** Uso de contexto arquitetural para redução de investigação manual

---

## 💡 Conceitos-chave

- **Impact scoring:** Calcular o impacto de uma falha baseado em dependências downstream
- **Business context:** Priorizar pelo impacto ao usuário/negócio, não pela severidade técnica isolada
- **Triage automation:** Automatizar a triagem inicial com base em score

---

## 📂 Arquivos deste vídeo

```
video-1.3-priorizacao/
├── README.md              ← Este arquivo
└── impact_scorer.py       ← Scoring de impacto baseado em topologia e contexto
```

## ▶️ Como executar

```bash
python3 aula-01-volume-de-sinais/video-1.3-priorizacao/impact_scorer.py
```
