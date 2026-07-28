# Vídeo 5.2 — Argo Rollouts: AnalysisTemplate e Experiment

## 🎬 Roteiro

**Tipo:** Apresentar Solução  
**Habilidade:** Escrever funcionalidades avançadas do Argo Rollouts — um `AnalysisTemplate` com múltiplas métricas consultando Prometheus e um `Experiment` que roda baseline vs. canary em paralelo — e simular a avaliação que decide promover ou abortar.

### Desenvolvimento

1. **Cenário real:** Um canary no Kubernetes precisa de gates de análise automáticos ligados às métricas reais do cluster, não a cliques manuais
2. **Solução:** O Argo Rollouts avalia `AnalysisTemplate`s (successRate, latência) via queries Prometheus e usa `Experiment` para comparar réplicas baseline e canary lado a lado

---

## 💡 Conceitos-chave

- **AnalysisTemplate:** recurso `argoproj.io/v1alpha1` com métricas, queries e condições de sucesso/falha
- **Metric provider:** origem dos dados (Prometheus, Datadog, Job, web...)
- **successCondition / failureCondition:** expressões que decidem cada medição
- **failureLimit:** número de medições ruins toleradas antes de abortar o Rollout
- **Experiment:** roda ReplicaSets baseline e canary em paralelo por tempo limitado para comparação justa

---

## 📂 Arquivos deste vídeo

```
video-5.2-argo-rollouts-features/
├── README.md          ← Este arquivo
└── argo_advanced.py   ← Gera YAMLs reais + simula avaliação das métricas
```

## ▶️ Como executar

```bash
python3 curso4-aula-05-ferramentas-praticas/video-5.2-argo-rollouts-features/argo_advanced.py
```

Comandos reais correspondentes (com o cluster e o plugin instalados):

```bash
kubectl argo rollouts get rollout checkout-api --watch
kubectl argo rollouts get experiment baseline-vs-canary
kubectl argo rollouts promote checkout-api
kubectl argo rollouts abort   checkout-api
```
