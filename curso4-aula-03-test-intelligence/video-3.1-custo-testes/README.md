# Vídeo 3.1 — O custo invisível de uma suíte de testes que só cresce

## 🎬 Roteiro

**Tipo:** Apresentar Contexto  
**Habilidade:** Quantificar o custo acumulado de uma suíte de testes que cresce a cada release e entender como isso degrada a produtividade do time.

### Desenvolvimento

1. **Cenário real:** Uma suíte que começou com 200 testes e chega a milhares ao longo das releases
2. **Teoria:** Tempo total de CI, feedback loop, minutos de runner desperdiçados e o efeito na produtividade

---

## 💡 Conceitos-chave

- **Tempo total de CI:** Soma do tempo de todos os testes (multiplicado pela paralelização)
- **Feedback loop:** Quanto o dev espera para saber se o commit quebrou algo
- **Minutos de runner desperdiçados:** Testes que rodam sem relação com a mudança
- **Custo de context switch:** Feedback lento força o dev a trocar de tarefa e perder foco

---

## 📂 Arquivos deste vídeo

```
video-3.1-custo-testes/
├── README.md              ← Este arquivo
└── test_suite_cost.py     ← Simulação do custo acumulado da suíte ao longo das releases
```

## ▶️ Como executar

```bash
python3 curso4-aula-03-test-intelligence/video-3.1-custo-testes/test_suite_cost.py
```
