# Vídeo 1.3 — Um modelo de risco de deploy com regressão logística

## 🎬 Roteiro

**Tipo:** Apresentar Solução  
**Habilidade:** Treinar e interpretar um classificador que transforma um feature vector em um risk score de 0 a 100.

### Desenvolvimento

1. **Cenário real:** Sair da correlação manual para um modelo que aprende os pesos
2. **Teoria:** Regressão logística, probabilidade → score, avaliação e interpretação

---

## 💡 Conceitos-chave

- **Regressão logística:** Modelo linear que produz uma probabilidade calibrada de falha
- **Risk score 0–100:** A probabilidade prevista, reescalada para leitura humana
- **Acurácia e matriz de confusão:** Como saber se o modelo acerta (e onde erra)
- **Pesos das features:** Coeficientes que tornam o modelo interpretável (por que este score?)

---

## 📂 Arquivos deste vídeo

```
video-1.3-modelo-risco-deploy/
├── README.md              ← Este arquivo
└── deploy_risk_model.py   ← Treino, avaliação e interpretação do modelo
```

## ▶️ Como executar

```bash
python3 curso4-aula-01-analise-risco-predeploy/video-1.3-modelo-risco-deploy/deploy_risk_model.py
```
