# Vídeo 3.2 — Análise de logs com IA

## 🎬 Roteiro

**Tipo:** Mostrar Solução  
**Habilidade:** Aplicar estratégias de chunking e extração de padrões para análise de logs com LLMs.

### Desenvolvimento

1. **Problema:** Logs de produção têm milhões de linhas — como enviar para um LLM com limite de tokens?
2. **Chunking:** Estratégias para dividir logs em blocos analisáveis
3. **Pattern extraction:** Extrair padrões relevantes antes de enviar ao modelo
4. **Demo:** Executar `log_analyzer_ai.py` e ver a extração de anomalias e padrões de erro

---

## 💡 Conceitos-chave

- **Chunking:** Divisão de textos longos em blocos menores para caber na context window do LLM
- **Token limit:** Restrição do número de tokens que um modelo pode processar por requisição
- **Pattern extraction:** Pré-processamento para filtrar apenas linhas relevantes antes do LLM
- **Log aggregation:** Agrupar linhas similares para reduzir volume (ex: 1000 erros iguais → 1 padrão)
- **Sliding window:** Técnica de análise que processa blocos sobrepostos de logs para não perder contexto

---

## 📂 Arquivos deste vídeo

```
video-3.2-analise-logs/
├── README.md            ← Este arquivo
└── log_analyzer_ai.py   ← Chunking e extração de padrões para análise com LLM
```

## ▶️ Como executar

```bash
python3 aula-03-investigacao-assistida-ia/video-3.2-analise-logs/log_analyzer_ai.py
```
