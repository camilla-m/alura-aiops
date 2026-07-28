# Vídeo 4.5 — Hands-on: Otimizando um pipeline de ponta a ponta

## 🎬 Roteiro

**Tipo:** Prática guiada  
**Habilidade:** Aplicar gargalos + paralelismo/cache + skip em um pipeline de exemplo e medir o ganho before/after.

### Desenvolvimento

1. **Setup:** Definir um pipeline realista como estrutura de dados (YAML embutido)
2. **Prática:** Rodar o funil de otimização e ler o relatório de minutos economizados

---

## 💡 Conceitos-chave

- **Pipeline como dado:** Descrever stages, dependências e inputs de forma declarativa
- **Funil de otimização:** Gargalos → paralelismo → cache → skip, em sequência
- **Relatório before/after:** Tempo total e minutos economizados em cada etapa
- **Fechamento da aula:** Otimização contínua guiada por evidência

---

## 📂 Arquivos deste vídeo

```
video-4.5-hands-on/
├── README.md                       ← Este arquivo
└── pipeline_optimization_lab.py    ← Laboratório before/after completo
```

## ▶️ Como executar

```bash
python3 curso4-aula-04-pipelines-auto-otimizaveis/video-4.5-hands-on/pipeline_optimization_lab.py
```
