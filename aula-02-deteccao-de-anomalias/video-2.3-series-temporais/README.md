# Vídeo 2.3 — Análise operacional de métricas e séries temporais

## 🎬 Roteiro

**Tipo:** Mostrar Solução  
**Habilidade:** Aplicar regressão linear em séries temporais para identificar tendências e prever esgotamento de recursos.

### Desenvolvimento

1. **Contexto:** Disco crescendo continuamente — quando vai estourar?
2. **Regressão linear:** Como ajustar uma reta à série histórica e projetar o futuro
3. **TTL (Time-To-Limit):** Calcular em quantos dias o recurso será esgotado
4. **Demo:** Executar `time_series_analysis.py` e visualizar a projeção de crescimento

---

## 💡 Conceitos-chave

- **Série temporal:** Sequência de valores medidos em intervalos regulares ao longo do tempo
- **Tendência (trend):** Direção geral de crescimento ou decrescimento de uma métrica
- **Regressão linear:** Técnica para ajustar uma reta (y = ax + b) a dados históricos
- **TTL (Time-To-Limit):** Previsão de quando um recurso atingirá seu limite máximo
- **Capacity planning:** Processo de antecipar necessidades de recursos com base em tendências
- **Forecast:** Projeção de valores futuros com base em padrões históricos

---

## 📂 Arquivos deste vídeo

```
video-2.3-series-temporais/
├── README.md                ← Este arquivo
└── time_series_analysis.py  ← Análise de tendência e forecast de capacidade
```

## ▶️ Como executar

```bash
python3 aula-02-deteccao-de-anomalias/video-2.3-series-temporais/time_series_analysis.py
```
