# Vídeo 2.3 — Argo Rollouts: o Rollout e o AnalysisTemplate na prática

## 🎬 Roteiro

**Tipo:** Apresentar Solução  
**Habilidade:** Escrever os manifests do [Argo Rollouts](https://argo-rollouts.readthedocs.io/) que descrevem uma estratégia canária com gates de análise, e entender como o controller os executa em runtime.

### Desenvolvimento

1. **Cenário real:** Traduzir "sobe em degraus e só promove se as métricas passarem" para YAML declarativo
2. **Solução:** Um recurso `Rollout` com steps (`setWeight` / `pause` / `analysis`) + um `AnalysisTemplate` com as métricas do gate; depois simular a execução

---

## 💡 Conceitos-chave

- **Rollout (`argoproj.io/v1alpha1`):** Substitui o `Deployment` e adiciona `strategy.canary` com `steps`
- **steps:** `setWeight 20 → pause → setWeight 50 → analysis → setWeight 100`
- **AnalysisTemplate:** Métricas com `successCondition` e `failureLimit` (aqui via provider Prometheus)
- **Promoção vs abort:** O controller avança quando a análise passa e faz rollback automático quando falha
- **Declarativo:** O mesmo YAML gera desfechos diferentes; quem decide é a análise, não o pipeline

---

## 📂 Arquivos deste vídeo

```
video-2.3-argo-rollouts/
├── README.md                    ← Este arquivo
├── argo_rollouts_simulator.py   ← Gera os manifests e simula os steps
├── rollout.yaml                 ← Gerado ao rodar o script (kind: Rollout)
└── analysis-template.yaml       ← Gerado ao rodar o script (kind: AnalysisTemplate)
```

## ▶️ Como executar

```bash
python3 curso4-aula-02-progressive-delivery/video-2.3-argo-rollouts/argo_rollouts_simulator.py
```

Num cluster real com o controller instalado:

```bash
kubectl apply -f rollout.yaml -f analysis-template.yaml
kubectl argo rollouts get rollout mapi-api --watch
```
