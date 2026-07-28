# Vídeo 3.2 — Test selection: rodando só os testes impactados pelo diff

## 🎬 Roteiro

**Tipo:** Apresentar Solução  
**Habilidade:** Manter um mapa de código → testes e selecionar, para cada diff, apenas o subconjunto de testes que exercita o código alterado.

### Desenvolvimento

1. **Cenário real:** Um diff toca 3 arquivos — por que rodar os 900 testes da suíte?
2. **Solução:** Mapa de cobertura invertido + seleção por arquivos alterados, validando que nenhum teste relevante foi perdido

---

## 💡 Conceitos-chave

- **Coverage map:** Relação arquivo_de_código → testes que o cobrem, construída a partir de dados de cobertura
- **Test selection:** Selecionar apenas os testes ligados aos arquivos do diff
- **Safety net:** Testes sem mapeamento (novos/desconhecidos) sempre entram por segurança
- **Economia %:** Redução de testes e de tempo vs. rodar a suíte inteira

---

## 📂 Arquivos deste vídeo

```
video-3.2-test-selection/
├── README.md            ← Este arquivo
└── test_selection.py    ← Mapa de cobertura + seleção de testes por diff
```

## ▶️ Como executar

```bash
python3 curso4-aula-03-test-intelligence/video-3.2-test-selection/test_selection.py
```
