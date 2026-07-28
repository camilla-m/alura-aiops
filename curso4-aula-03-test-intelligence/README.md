# Aula 3 — Test intelligence: rodando só os testes que importam

## 🎯 Objetivo de aprendizagem

Aplicar Machine Learning e análise de dados ao pipeline de testes para executar apenas os testes relevantes a cada mudança (test selection), detectar testes instáveis (flaky) e otimizar continuamente a suíte, reduzindo o custo de CI sem perder cobertura.

---

## 📹 Vídeos

| Vídeo | Título | Tipo |
|-------|--------|------|
| 3.1 | O custo invisível de uma suíte de testes que só cresce | Contexto |
| 3.2 | Test selection: rodando só os testes impactados pelo diff | Solução |
| 3.3 | Flaky tests: detectando instabilidade sem mudança de código | Solução |
| 3.4 | Test impact analysis: redundância, gaps e testes de alto valor | Teoria |
| 3.5 | Hands-on: pipeline completo de test intelligence | Prática |

---

## 🏗️ Estrutura

```
curso4-aula-03-test-intelligence/
├── README.md                          ← Este arquivo
├── video-3.1-custo-testes/            ← Contexto: O custo acumulado da suíte
├── video-3.2-test-selection/          ← Solução: Seleção de testes por diff
├── video-3.3-flaky-tests/             ← Solução: Detecção de flaky tests
├── video-3.4-test-impact/             ← Teoria: Análise de impacto e cobertura
└── video-3.5-hands-on/                ← Prática: Pipeline de ponta a ponta
```

---

## 🧩 Habilidades desenvolvidas

- Quantificar o custo real de CI: tempo total, feedback loop e minutos de runner desperdiçados
- Construir um mapa arquivo → testes e selecionar o subconjunto impactado por um diff
- Detectar flaky tests a partir de histórico de execuções e priorizar quarentena/fix
- Identificar testes redundantes, gaps de cobertura e testes de alto valor
- Montar um pipeline de test intelligence que decide o que rodar e reporta o resultado
