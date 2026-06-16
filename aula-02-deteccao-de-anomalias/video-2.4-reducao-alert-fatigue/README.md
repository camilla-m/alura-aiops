# Vídeo 2.4 — Redução de alert fatigue

## 🎬 Roteiro

**Tipo:** Apresentar Problema + Mostrar Solução  
**Habilidade:** Auditar a qualidade de um catálogo de alertas e identificar fontes de ruído operacional.

### Desenvolvimento

1. **O problema:** Mostrar estatísticas reais de alert fatigue em operações de cloud
2. **SNR (Signal-to-Noise Ratio):** Apresentar a métrica que mede a "utilidade" de um alerta
3. **Auditoria do catálogo:** Como analisar o histórico de alertas para encontrar os ruidosos
4. **Demo:** Executar `alert_fatigue_analyzer.py` e identificar os alertas candidatos à desativação

---

## 💡 Conceitos-chave

- **Alert fatigue:** Condição em que o volume excessivo de alertas leva à dessensibilização do time
- **SNR (Signal-to-Noise Ratio):** Razão entre alertas acionáveis e alertas sem ação associada
- **Actionable alert:** Alerta que resulta diretamente em uma ação humana ou automática
- **Noisy alert:** Alerta que é ignorado, resolvido automaticamente ou que não exige intervenção
- **Alert catalog audit:** Revisão sistemática de todos os alertas configurados para eliminar ruído
- **False positive rate:** Porcentagem de alertas que não representam problemas reais

---

## 📂 Arquivos deste vídeo

```
video-2.4-reducao-alert-fatigue/
├── README.md                  ← Este arquivo
└── alert_fatigue_analyzer.py  ← Análise de SNR e qualidade do catálogo de alertas
```

## ▶️ Como executar

```bash
python3 aula-02-deteccao-de-anomalias/video-2.4-reducao-alert-fatigue/alert_fatigue_analyzer.py
```
