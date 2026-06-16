# Vídeo 3.4 — Contexto distribuído para LLMs

## 🎬 Roteiro

**Tipo:** Explicar Teoria + Mostrar Solução  
**Habilidade:** Serializar topologia de serviços e contexto distribuído em formato adequado para consumo por LLMs.

### Desenvolvimento

1. **Problema:** Um incidente em microsserviços envolve 10+ serviços — como dar contexto completo ao LLM sem estourar tokens?
2. **Serialização de topologia:** Converter o grafo de dependências em texto estruturado
3. **Context packing:** Priorizar quais informações incluir no prompt dado o limite de tokens
4. **Demo:** Executar `topology_context.py` e ver o mapa de serviços serializado para o LLM

---

## 💡 Conceitos-chave

- **Service dependency graph:** Mapa de dependências entre microsserviços (quem chama quem)
- **Context serialization:** Converter estruturas de dados (grafos, dicts) em texto para o LLM
- **Token budget:** Gerenciar o espaço disponível no prompt para incluir o máximo de contexto relevante
- **Topological ordering:** Ordenar serviços do mais crítico ao menos crítico para priorizar o contexto
- **Distributed tracing context:** Como trace_id e span_id conectam eventos em sistemas distribuídos

---

## 📂 Arquivos deste vídeo

```
video-3.4-contexto-distribuido/
├── README.md               ← Este arquivo
└── topology_context.py     ← Serialização de topologia distribuída para prompts de LLM
```

## ▶️ Como executar

```bash
python3 aula-03-investigacao-assistida-ia/video-3.4-contexto-distribuido/topology_context.py
```
