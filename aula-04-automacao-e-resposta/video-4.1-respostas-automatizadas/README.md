# Vídeo 4.1 — Respostas automatizadas e self-healing

## 🎬 Roteiro

**Tipo:** Apresentar Contexto + Mostrar Solução  
**Habilidade:** Estruturar fluxos de remediação automatizada com máquina de estados e guardrails.

### Desenvolvimento

1. **Problema:** Ações manuais repetitivas em incidentes — reiniciar pod, escalar réplicas, limpar cache
2. **Self-healing:** Como automatizar essas ações de forma segura e auditável
3. **State machine:** Modelar o ciclo de vida de um incidente como estados e transições
4. **Demo:** Executar `self_healing_engine.py` e ver o motor diagnosticando e remediando automaticamente

---

## 💡 Conceitos-chave

- **Self-healing:** Capacidade do sistema de se recuperar automaticamente de falhas conhecidas
- **State machine:** Modelo que representa estados (DETECTED → DIAGNOSING → REMEDIATING → RESOLVED) e transições
- **Runbook automation:** Executar procedimentos operacionais documentados de forma automática
- **Idempotency:** Garantia que executar a mesma ação múltiplas vezes tem o mesmo resultado final
- **Event-driven remediation:** Acionar remediação automaticamente baseado em eventos, não em polling

---

## 📂 Arquivos deste vídeo

```
video-4.1-respostas-automatizadas/
├── README.md                ← Este arquivo
└── self_healing_engine.py   ← Motor de self-healing com máquina de estados
```

## ▶️ Como executar

```bash
python3 aula-04-automacao-e-resposta/video-4.1-respostas-automatizadas/self_healing_engine.py
```
