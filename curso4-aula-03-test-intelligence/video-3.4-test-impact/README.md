# Vídeo 3.4 — Test impact analysis: redundância, gaps e testes de alto valor

## 🎬 Roteiro

**Tipo:** Apresentar Teoria  
**Habilidade:** A partir de um coverage map (teste → linhas/funcionalidades cobertas), identificar testes redundantes, gaps de cobertura e testes de alto valor, sugerindo a consolidação da suíte.

### Desenvolvimento

1. **Teoria:** Cobertura como conjunto — interseção, subconjunto e cobertura única
2. **Aplicação:** Classificar cada teste e propor uma suíte enxuta que mantém a cobertura

---

## 💡 Conceitos-chave

- **Teste redundante:** Sua cobertura é subconjunto da de outro (não adiciona nada)
- **Gap de cobertura:** Funcionalidade/linha sem nenhum teste associado
- **Cobertura única:** Linhas que só aquele teste cobre (o que se perde ao removê-lo)
- **Teste de alto valor:** Muita cobertura única e/ou cobre áreas críticas por baixo custo

---

## 📂 Arquivos deste vídeo

```
video-3.4-test-impact/
├── README.md                  ← Este arquivo
└── test_impact_analysis.py    ← Redundância, gaps, alto valor e consolidação
```

## ▶️ Como executar

```bash
python3 curso4-aula-03-test-intelligence/video-3.4-test-impact/test_impact_analysis.py
```
