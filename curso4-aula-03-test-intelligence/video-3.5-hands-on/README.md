# Vídeo 3.5 — Hands-on: pipeline completo de test intelligence

## 🎬 Roteiro

**Tipo:** Prática (Hands-on)  
**Habilidade:** Montar um pipeline de ponta a ponta que recebe um diff, faz test selection, "roda" os testes selecionados, filtra flaky com retry e reporta o resultado final (verde/vermelho) e o tempo economizado.

### Desenvolvimento

1. **Integração:** Amarrar selection (3.2) + flaky (3.3) + custo (3.1) em um fluxo único
2. **Resultado:** Veredito do build e economia vs. rodar a suíte inteira

---

## 💡 Conceitos-chave

- **Pipeline de test intelligence:** diff → selection → execução → filtro flaky → veredito
- **Retry de flaky:** Um teste flaky que falha é re-executado antes de reprovar o build
- **Veredito:** Verde só se todos os testes reais passam; flaky não derruba o build
- **Tempo economizado:** Comparação direta com a estratégia "rodar tudo"

---

## 📂 Arquivos deste vídeo

```
video-3.5-hands-on/
├── README.md                    ← Este arquivo
└── test_intelligence_lab.py     ← Pipeline completo de ponta a ponta
```

## ▶️ Como executar

```bash
python3 curso4-aula-03-test-intelligence/video-3.5-hands-on/test_intelligence_lab.py
```
