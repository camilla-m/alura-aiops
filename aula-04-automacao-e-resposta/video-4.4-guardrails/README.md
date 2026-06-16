# Vídeo 4.4 — Guardrails e automação segura

## 🎬 Roteiro

**Tipo:** Apresentar Contexto + Mostrar Solução  
**Habilidade:** Implementar camadas de proteção que tornam a automação segura para produção.

### Desenvolvimento

1. **Problema:** Automação sem limites pode piorar incidentes — deletar dados, reiniciar serviços críticos
2. **Guardrails:** Camada de validação obrigatória antes de qualquer ação automática
3. **Blast radius estimation:** Calcular o impacto máximo de uma ação antes de executá-la
4. **Human-in-the-loop:** Quando a automação deve parar e pedir aprovação humana
5. **Demo:** Executar `guardrail_engine.py` e ver ações bloqueadas, aprovadas e escaladas

---

## 💡 Conceitos-chave

- **Guardrails:** Regras que limitam o escopo e impacto de ações automatizadas
- **Blast radius:** Estimativa do número de serviços/usuários afetados por uma ação
- **Circuit breaker:** Mecanismo que para automações quando a taxa de erro ultrapassa um threshold
- **Human-in-the-loop:** Ponto no fluxo automatizado onde aprovação humana é obrigatória
- **Least privilege automation:** Princípio de conceder à automação apenas as permissões mínimas necessárias
- **Action risk score:** Pontuação de risco calculada para cada ação antes da execução

---

## 📂 Arquivos deste vídeo

```
video-4.4-guardrails/
├── README.md              ← Este arquivo
└── guardrail_engine.py    ← Motor de guardrails com circuit breaker e aprovação humana
```

## ▶️ Como executar

```bash
python3 aula-04-automacao-e-resposta/video-4.4-guardrails/guardrail_engine.py
```
