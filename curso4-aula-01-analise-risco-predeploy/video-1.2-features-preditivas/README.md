# Vídeo 1.2 — Features preditivas: o que torna um deploy perigoso

## 🎬 Roteiro

**Tipo:** Teoria  
**Habilidade:** Transformar sinais brutos de commits e PRs em um vetor numérico de features que um modelo consegue aprender.

### Desenvolvimento

1. **Cenário real:** Um lote de PRs com mensagem e estatísticas de diff
2. **Teoria:** Do diff bruto ao feature vector; correlação de cada feature com falha

---

## 💡 Conceitos-chave

- **Code churn:** Volume de mudança (linhas adicionadas + removidas) como proxy de risco
- **Cobertura de testes:** Fração do código tocado que está sob teste
- **Complexidade ciclomática estimada:** Aproximação a partir de palavras-chave de controle de fluxo
- **Feature vector:** Representação numérica padronizada de um PR, pronta para o modelo
- **Correlação feature ↔ falha:** Ranking de quais sinais mais se associam a deploys que quebram

---

## 📂 Arquivos deste vídeo

```
video-1.2-features-preditivas/
├── README.md               ← Este arquivo
└── feature_extraction.py   ← Extração de features e ranking por correlação
```

## ▶️ Como executar

```bash
python3 curso4-aula-01-analise-risco-predeploy/video-1.2-features-preditivas/feature_extraction.py
```
