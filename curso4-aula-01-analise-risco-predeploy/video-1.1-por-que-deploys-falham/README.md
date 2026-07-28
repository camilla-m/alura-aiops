# Vídeo 1.1 — Por que deploys falham? Anatomia do risco

## 🎬 Roteiro

**Tipo:** Apresentar Contexto  
**Habilidade:** Reconhecer que falhas de deploy não são aleatórias e sim correlacionadas a fatores mensuráveis do próprio deploy.

### Desenvolvimento

1. **Cenário real:** Um histórico de ~200 deploys e a pergunta "dava para prever?"
2. **Teoria:** Taxa de falha global vs. taxa de falha condicionada a cada fator de risco

---

## 💡 Conceitos-chave

- **Taxa de falha global:** Baseline de quantos deploys quebram, sem olhar nenhum fator
- **Fator de risco:** Atributo do deploy (migration, sexta à noite, autor júnior) que desloca a probabilidade de falha
- **Lift:** Quantas vezes um fator aumenta o risco em relação ao baseline
- **Deploy risk score:** Ideia de agregar os fatores em um único número — semente para o modelo dos próximos vídeos

---

## 📂 Arquivos deste vídeo

```
video-1.1-por-que-deploys-falham/
├── README.md                    ← Este arquivo
└── deploy_failure_analysis.py   ← Análise estatística de um histórico de deploys
```

## ▶️ Como executar

```bash
python3 curso4-aula-01-analise-risco-predeploy/video-1.1-por-que-deploys-falham/deploy_failure_analysis.py
```
