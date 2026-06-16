# Vídeo 4.5 — Hands-on: Pipeline de automação completo

## 🎬 Roteiro

**Tipo:** Prática Guiada  
**Habilidade:** Integrar diagnóstico, guardrails, runbooks e comunicação em um pipeline de automação end-to-end.

### Desenvolvimento

1. **Exercício 1:** Disparar o motor de self-healing com um incidente simulado
2. **Exercício 2:** Passar pela camada de guardrails e ver ações bloqueadas vs. aprovadas
3. **Exercício 3:** Executar o runbook correspondente com auditoria
4. **Exercício 4:** Gerar comunicações automáticas e o rascunho de post-mortem

---

## 💡 O que você vai praticar

- Integrar os módulos de self-healing, guardrails e runbooks
- Verificar o audit trail de todas as ações executadas
- Simular a aprovação humana no fluxo de automação
- Gerar comunicações automáticas para diferentes audiências

---

## 📂 Arquivos deste vídeo

```
video-4.5-hands-on/
├── README.md           ← Este arquivo
└── automation_lab.py   ← Lab de automação end-to-end com guardrails e runbooks
```

## ▶️ Como executar

```bash
python3 aula-04-automacao-e-resposta/video-4.5-hands-on/automation_lab.py
```

---

## 🎓 Ao final deste hands-on você terá:

- ✔ Executado um pipeline completo de self-healing
- ✔ Validado guardrails em ações de risco alto e baixo
- ✔ Gerado um audit trail rastreável de todas as ações
- ✔ Produzido comunicações e rascunho de post-mortem automaticamente
