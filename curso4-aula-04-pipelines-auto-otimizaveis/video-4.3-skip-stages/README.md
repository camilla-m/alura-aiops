# Vídeo 4.3 — Skip seguro de stages por análise de diff

## 🎬 Roteiro

**Tipo:** Apresentar Solução  
**Habilidade:** Decidir com segurança quais stages podem ser pulados a partir do conteúdo do diff de mudanças.

### Desenvolvimento

1. **Cenário real:** Um PR que só toca `docs/` roda o pipeline inteiro sem necessidade
2. **Teoria:** Regras de impacto por caminho de arquivo e o custo de um skip errado

---

## 💡 Conceitos-chave

- **Análise de diff:** Classificar as mudanças pelos caminhos afetados
- **Regras de impacto:** Mapear categorias de arquivo aos stages que realmente afetam
- **Skip seguro:** Pular só quando há garantia de que o stage não muda de resultado
- **Fail-safe:** Na dúvida, NÃO pular — rodar o stage é o padrão conservador

---

## 📂 Arquivos deste vídeo

```
video-4.3-skip-stages/
├── README.md                  ← Este arquivo
└── conditional_execution.py   ← Decisão de skip por regras sobre o diff
```

## ▶️ Como executar

```bash
python3 curso4-aula-04-pipelines-auto-otimizaveis/video-4.3-skip-stages/conditional_execution.py
```
