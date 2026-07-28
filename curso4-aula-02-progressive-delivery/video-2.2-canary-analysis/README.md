# Vídeo 2.2 — Canary analysis: decidir promover ou reverter com estatística

## 🎬 Roteiro

**Tipo:** Apresentar Solução  
**Habilidade:** Decidir a promoção ou a reversão de um canary a partir de significância estatística, e não da leitura visual de um gráfico.

### Desenvolvimento

1. **Cenário real:** O canary parece "um pouquinho pior" — isso é regressão ou é ruído?
2. **Solução:** z-test de proporção para a taxa de erro + Mann-Whitney U para a latência p95, com decisão por p-value

---

## 💡 Conceitos-chave

- **Baseline vs canary:** Comparar a versão stable com a versão nova sob o mesmo tráfego
- **z-test de proporção:** Testa se a taxa de erro do canary é significativamente maior (uma cauda)
- **Mann-Whitney U:** Compara distribuições de latência sem assumir normalidade (bom para caudas de p95)
- **alpha e p-value:** `alpha` é o risco aceito de reverter à toa; só reverte quando `p < alpha`
- **PROMOTE / ROLLBACK / INCONCLUSIVE:** Amostra pequena não conclui nada — pede mais dados

---

## 📂 Arquivos deste vídeo

```
video-2.2-canary-analysis/
├── README.md            ← Este arquivo
└── canary_analysis.py   ← Compara baseline vs canary e decide com p-value
```

> Usa `scipy.stats` quando disponível (motor de produção) e cai em uma
> implementação equivalente em stdlib quando o scipy não está instalado,
> para rodar em qualquer ambiente sem rede.

## ▶️ Como executar

```bash
python3 curso4-aula-02-progressive-delivery/video-2.2-canary-analysis/canary_analysis.py
```
