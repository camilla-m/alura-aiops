# Vídeo 5.4 — Buildkite Test Analytics: reliability, flaky e slow tests

## 🎬 Roteiro

**Tipo:** Apresentar Solução  
**Habilidade:** Reproduzir o Buildkite Test Analytics — ingerir resultados de testes de vários builds, calcular reliability por teste, detectar slow tests e flaky tests, mostrar tendências (p95 de duração, taxa de falha) e emitir um test health report.

### Desenvolvimento

1. **Cenário real:** A suíte fica vermelha às vezes, mas ninguém sabe quais testes são realmente instáveis nem quais dominam o tempo de CI
2. **Solução:** Um analytics de testes que agrega execuções por teste, mede confiabilidade, identifica flakes e slow tests e reporta tendências

---

## 💡 Conceitos-chave

- **Reliability:** % de execuções que passaram para um teste ao longo dos builds
- **Flaky test:** teste que passa e falha sem mudança de código (resultados mistos no mesmo commit)
- **Slow test:** teste no topo da distribuição de duração (p95)
- **Trends:** evolução da taxa de falha e da duração ao longo do tempo
- **Test health report:** ranking dos testes que mais custam confiabilidade e tempo

---

## 📂 Arquivos deste vídeo

```
video-5.4-buildkite-analytics/
├── README.md               ← Este arquivo
└── buildkite_analytics.py  ← Ingestão de execuções + reliability + flaky/slow + report
```

## ▶️ Como executar

```bash
python3 curso4-aula-05-ferramentas-praticas/video-5.4-buildkite-analytics/buildkite_analytics.py
```
