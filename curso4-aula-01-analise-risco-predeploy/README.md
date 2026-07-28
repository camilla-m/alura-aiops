# Aula 1 — Análise de risco pré-deploy

## 🎯 Objetivo de aprendizagem

Usar dados históricos e machine learning para prever e barrar deploys arriscados antes que cheguem à produção, transformando o CI/CD em um portão de decisão inteligente.

---

## 📹 Vídeos

| Vídeo | Título | Tipo |
|-------|--------|------|
| 1.1 | Por que deploys falham? Anatomia do risco | Contexto |
| 1.2 | Features preditivas: o que torna um deploy perigoso | Teoria |
| 1.3 | Um modelo de risco de deploy com regressão logística | Solução |
| 1.4 | Risk score no pipeline: o gate de CI | Solução |
| 1.5 | Hands-on: pipeline de risco de ponta a ponta | Prática |

---

## 🏗️ Estrutura

```
curso4-aula-01-analise-risco-predeploy/
├── README.md                          ← Este arquivo
├── video-1.1-por-que-deploys-falham/  ← Contexto: análise estatística de falhas
├── video-1.2-features-preditivas/     ← Teoria: extração de features de PRs
├── video-1.3-modelo-risco-deploy/     ← Solução: modelo de risco (LogisticRegression)
├── video-1.4-risk-score-pipeline/     ← Solução: gate PASS/WARN/BLOCK no CI
└── video-1.5-hands-on/                ← Prática: pipeline end-to-end
```

---

## 🧩 Habilidades desenvolvidas

- Quantificar o risco de deploy a partir de histórico operacional (fatores como migrations, horário, experiência do autor)
- Extrair features preditivas de commits e pull requests (code churn, cobertura, complexidade, idade do código)
- Treinar e interpretar um modelo de classificação para gerar um risk score 0–100
- Construir um gate de CI que decide PASS / WARN / BLOCK com thresholds configuráveis e escala para revisão humana
- Integrar dados, modelo e gate em um pipeline de risco automatizado de ponta a ponta
