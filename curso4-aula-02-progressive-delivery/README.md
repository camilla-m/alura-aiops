# Aula 2 — Progressive delivery assistido

## 🎯 Objetivo de aprendizagem

Aplicar canary analysis automatizada com significância estatística e Argo Rollouts para promover ou reverter deploys com segurança, transformando o release em uma decisão baseada em dados em vez de coragem.

---

## 📹 Vídeos

| Vídeo | Título | Tipo |
|-------|--------|------|
| 2.1 | Progressive delivery: canary, blue-green e feature flags | Contexto |
| 2.2 | Canary analysis: decidir promover ou reverter com estatística | Solução |
| 2.3 | Argo Rollouts: o Rollout e o AnalysisTemplate na prática | Solução |
| 2.4 | Rollback inteligente: detectar degradação e reverter sozinho | Solução |
| 2.5 | Hands-on: rollout canário de ponta a ponta | Prática |

---

## 🏗️ Estrutura

```
curso4-aula-02-progressive-delivery/
├── README.md                              ← Este arquivo
├── video-2.1-progressive-delivery-revisao/ ← Contexto: estratégias e blast radius
├── video-2.2-canary-analysis/             ← Solução: z-test + Mann-Whitney → decisão
├── video-2.3-argo-rollouts/               ← Solução: gera YAML real e simula os steps
├── video-2.4-rollback-inteligente/        ← Solução: rollback automático por janela
└── video-2.5-hands-on/                    ← Prática: canário end-to-end
```

---

## 🧩 Habilidades desenvolvidas

- Comparar canary, blue-green e feature flags por velocidade, custo, blast radius e granularidade
- Rodar canary analysis comparando baseline (stable) vs canary com testes estatísticos (z-test de proporção e Mann-Whitney de latência)
- Decidir PROMOTE / ROLLBACK / INCONCLUSIVE a partir de p-value e não de "achismo"
- Escrever manifests reais de Argo Rollouts (`Rollout` + `AnalysisTemplate`, `argoproj.io/v1alpha1`) com steps e gates de análise
- Implementar rollback automático por janelas e medir o ganho de blast radius e tempo de detecção vs rollback manual
- Integrar tráfego, análise e promoção/reversão em um pipeline de progressive delivery de ponta a ponta
