# Vídeo 1.5 — Hands-on: pipeline de risco de ponta a ponta

## 🎬 Roteiro

**Tipo:** Prática (mão na massa)  
**Habilidade:** Integrar dados, modelo e gate em um único pipeline que avalia PRs reais de exemplo.

### Desenvolvimento

1. **Cenário real:** Do dataset ao veredito, tudo em uma execução
2. **Prática:** Treinar o modelo e rodar o gate em 3 PRs (seguro, médio, perigoso)

---

## 💡 Conceitos-chave

- **Pipeline de risco end-to-end:** Dados → treino → score → decisão, encadeados
- **Racional da decisão:** Cada veredito acompanhado das features que o justificam
- **PR seguro vs. perigoso:** Ver o mesmo modelo reagir a três perfis de mudança
- **Fechamento:** Como esse gate se conecta ao restante do curso de CI/CD inteligente

---

## 📂 Arquivos deste vídeo

```
video-1.5-hands-on/
├── README.md                 ← Este arquivo
└── deploy_risk_pipeline.py   ← Pipeline completo: dataset + modelo + gate
```

## ▶️ Como executar

```bash
python3 curso4-aula-01-analise-risco-predeploy/video-1.5-hands-on/deploy_risk_pipeline.py
```
