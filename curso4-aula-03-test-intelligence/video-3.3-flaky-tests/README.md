# Vídeo 3.3 — Flaky tests: detectando instabilidade sem mudança de código

## 🎬 Roteiro

**Tipo:** Apresentar Solução  
**Habilidade:** Analisar o histórico de execuções e identificar testes flaky (que alternam pass/fail sem que o código tenha mudado), calcular um flakiness score e priorizar quarentena/fix.

### Desenvolvimento

1. **Cenário real:** Um teste "vermelho" no CI que fica verde ao rodar de novo, sem tocar em nada
2. **Solução:** Flakiness score a partir do histórico, quarentena dos piores e ranking de fix

---

## 💡 Conceitos-chave

- **Flaky test:** Resultado não determinístico (pass/fail) para o mesmo commit
- **Flakiness score:** Métrica que combina taxa de falha e nº de transições pass↔fail no mesmo commit
- **Quarentena:** Isolar o teste instável para não bloquear o pipeline enquanto é corrigido
- **Falha real vs. flaky:** Falha consistente após uma mudança de código NÃO é flakiness

---

## 📂 Arquivos deste vídeo

```
video-3.3-flaky-tests/
├── README.md              ← Este arquivo
└── flaky_detection.py     ← Flakiness score, quarentena e ranking de fix
```

## ▶️ Como executar

```bash
python3 curso4-aula-03-test-intelligence/video-3.3-flaky-tests/flaky_detection.py
```
