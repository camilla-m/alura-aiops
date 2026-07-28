# Vídeo 5.1 — Harness: Continuous Verification e governance gates

## 🎬 Roteiro

**Tipo:** Apresentar Solução  
**Habilidade:** Reproduzir o conceito de Continuous Verification do Harness — verificar automaticamente as métricas de um deploy contra a baseline e decidir promover, segurar ou fazer rollback via governance gates.

### Desenvolvimento

1. **Cenário real:** Após um deploy canário, o time não quer olhar dashboard manualmente — a plataforma precisa julgar a saúde sozinha
2. **Solução:** O Harness coleta métricas do provider (Prometheus, Datadog, etc.), compara canary vs. baseline com análise estatística e aplica um risk score + gates de governança

---

## 💡 Conceitos-chave

- **Continuous Verification (CV):** verificação automatizada de métricas pós-deploy contra uma janela de baseline
- **Risk score:** nota de 0 a 100 que resume o desvio do canary em relação ao baseline
- **Governance gates:** políticas que transformam o risk score em decisão (auto-approve, hold, rollback)
- **Auto-rollback:** reversão automática quando a verificação falha, sem intervenção humana

---

## 📂 Arquivos deste vídeo

```
video-5.1-harness/
├── README.md            ← Este arquivo
└── harness_ai_demo.py   ← Continuous Verification + governance gates simulados
```

## ▶️ Como executar

```bash
python3 curso4-aula-05-ferramentas-praticas/video-5.1-harness/harness_ai_demo.py
```
