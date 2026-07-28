# Aula 5 — Ferramentas na prática

## 🎯 Objetivo de aprendizagem

Conhecer e comparar ferramentas reais de CI/CD inteligente (Harness, Argo Rollouts, LaunchDarkly, Buildkite) reproduzindo seus conceitos centrais de forma local e simulada, e montar uma estratégia de adoção priorizada para uma organização.

---

## 📹 Vídeos

| Vídeo | Título | Tipo |
|-------|--------|------|
| 5.1 | Harness: Continuous Verification e governance gates | Solução |
| 5.2 | Argo Rollouts: AnalysisTemplate e Experiment | Solução |
| 5.3 | LaunchDarkly: feature flags com targeting e rollout | Solução |
| 5.4 | Buildkite Test Analytics: reliability, flaky e slow tests | Solução |
| 5.5 | Hands-on: Estratégia de adoção de CI/CD inteligente | Prática |

---

## 🏗️ Estrutura

```
curso4-aula-05-ferramentas-praticas/
├── README.md                          ← Este arquivo
├── video-5.1-harness/                 ← Harness Continuous Verification + gates
├── video-5.2-argo-rollouts-features/  ← AnalysisTemplate multi-métrica + Experiment
├── video-5.3-launchdarkly/            ← Feature-flag engine com targeting
├── video-5.4-buildkite-analytics/     ← Test Analytics: flaky, slow, reliability
└── video-5.5-estrategia/              ← Scorecard de maturidade + roadmap
```

---

## 🧩 Habilidades desenvolvidas

- Reproduzir o Continuous Verification do Harness: verificação automática pós-deploy contra baseline e governance gates
- Escrever AnalysisTemplate e Experiment reais do Argo Rollouts e simular a decisão de promover/abortar
- Implementar um mini feature-flag engine estilo LaunchDarkly com targeting rules e percentage rollout determinístico
- Analisar saúde de suíte de testes ao estilo Buildkite Test Analytics (reliability, flaky, slow tests, tendências)
- Avaliar a maturidade de CI/CD inteligente de uma organização e gerar um roadmap de adoção priorizado por quick wins
