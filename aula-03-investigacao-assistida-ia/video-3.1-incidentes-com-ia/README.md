# Vídeo 3.1 — Usando IA para diagnóstico de incidentes

## 🎬 Roteiro

**Tipo:** Apresentar Contexto + Mostrar Solução  
**Habilidade:** Estruturar prompts eficazes para diagnóstico de incidentes com LLMs.

### Desenvolvimento

1. **Problema:** Mostrar como o troubleshooting manual consome horas e depende de especialistas
2. **Conceito:** Como LLMs podem sintetizar logs, métricas e traces em segundos
3. **Prompt engineering:** Estruturar contexto de forma que a IA gere diagnósticos acionáveis
4. **Demo:** Executar `incident_ai_assistant.py` e ver a IA gerando hipóteses e passos de resolução

---

## 💡 Conceitos-chave

- **LLM para ops:** Usar modelos de linguagem como "analista sênior" que sintetiza múltiplas fontes de sinal
- **Prompt engineering:** Arte de estruturar o contexto para obter respostas precisas e acionáveis
- **System prompt:** Instrução que define o papel e comportamento do modelo
- **Context window:** Limite de tokens que define quanto contexto o LLM pode processar
- **RCA (Root Cause Analysis):** Identificação da causa raiz de um incidente de forma estruturada

---

## 📂 Arquivos deste vídeo

```
video-3.1-incidentes-com-ia/
├── README.md                  ← Este arquivo
└── incident_ai_assistant.py   ← Framework de prompts para diagnóstico com IA
```

## ▶️ Como executar

```bash
python3 aula-03-investigacao-assistida-ia/video-3.1-incidentes-com-ia/incident_ai_assistant.py
```
