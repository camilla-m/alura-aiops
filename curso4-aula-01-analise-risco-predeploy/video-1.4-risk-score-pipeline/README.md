# Vídeo 1.4 — Risk score no pipeline: o gate de CI

## 🎬 Roteiro

**Tipo:** Apresentar Solução  
**Habilidade:** Transformar o risk score em uma decisão automatizada de pipeline (PASS / WARN / BLOCK) com escalonamento para humanos.

### Desenvolvimento

1. **Cenário real:** O modelo dá um número — mas o CI precisa DECIDIR
2. **Teoria:** Thresholds configuráveis, faixas de decisão e exit codes

---

## 💡 Conceitos-chave

- **Gate de CI:** Etapa que aprova ou bloqueia o deploy com base no risco
- **Thresholds PASS/WARN/BLOCK:** Faixas de score que definem a ação (configuráveis)
- **Escalonamento humano:** WARN e BLOCK acionam revisão em vez de seguir cego
- **Exit code:** Código de saída que integra a decisão ao runner de CI (0 = ok, ≠0 = barrado)

---

## 📂 Arquivos deste vídeo

```
video-1.4-risk-score-pipeline/
├── README.md      ← Este arquivo
└── risk_gate.py   ← Gate de CI que decide PASS/WARN/BLOCK a partir do score
```

## ▶️ Como executar

```bash
python3 curso4-aula-01-analise-risco-predeploy/video-1.4-risk-score-pipeline/risk_gate.py
```
