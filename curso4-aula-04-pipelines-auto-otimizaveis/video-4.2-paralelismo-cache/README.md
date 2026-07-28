# Vídeo 4.2 — Paralelismo dinâmico e cache inteligente

## 🎬 Roteiro

**Tipo:** Apresentar Solução  
**Habilidade:** Modelar dependências entre stages como um DAG e calcular o paralelismo ótimo somado a cache inteligente.

### Desenvolvimento

1. **Cenário real:** Stages independentes rodando em série desperdiçam tempo
2. **Teoria:** Níveis topológicos, caminho crítico e cache hit por hash de inputs

---

## 💡 Conceitos-chave

- **DAG de dependências:** Grafo acíclico que descreve o que precisa terminar antes de quê
- **Níveis topológicos:** Stages sem dependência mútua rodam no mesmo nível, em paralelo
- **Caminho crítico:** Menor tempo possível mesmo com paralelismo infinito
- **Cache inteligente:** Stage com inputs inalterados vira cache hit (tempo ~0)

---

## 📂 Arquivos deste vídeo

```
video-4.2-paralelismo-cache/
├── README.md                     ← Este arquivo
└── parallel_cache_optimizer.py   ← DAG, paralelismo topológico e cache
```

## ▶️ Como executar

```bash
python3 curso4-aula-04-pipelines-auto-otimizaveis/video-4.2-paralelismo-cache/parallel_cache_optimizer.py
```
