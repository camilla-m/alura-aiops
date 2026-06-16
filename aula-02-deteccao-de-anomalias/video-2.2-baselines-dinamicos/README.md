# Vídeo 2.2 — Baselines dinâmicos e comportamento esperado

## 🎬 Roteiro

**Tipo:** Explicar Teoria + Mostrar Solução  
**Habilidade:** Construir e aplicar baselines dinâmicos que se adaptam à sazonalidade das métricas.

### Desenvolvimento

1. **Problema do threshold fixo:** Mostrar por que um limite estático falha em métricas com padrões semanais
2. **Conceito de EMA:** Explicar Exponential Moving Average como forma de capturar tendências recentes
3. **Bandas de confiança:** Como calcular o intervalo esperado (média ± N desvios) para cada hora do dia
4. **Demo:** Executar `dynamic_baseline.py` e observar as bandas se adaptando à sazonalidade

---

## 💡 Conceitos-chave

- **Baseline dinâmico:** Linha de referência que evolui com o comportamento histórico do sistema
- **EMA (Exponential Moving Average):** Média ponderada que dá mais peso aos dados recentes
- **Sazonalidade:** Padrões que se repetem em intervalos regulares (diário, semanal)
- **Banda de confiança:** Intervalo [média - Nσ, média + Nσ] que define o comportamento "normal"
- **Adaptive threshold:** Threshold que varia automaticamente com o contexto temporal

---

## 📂 Arquivos deste vídeo

```
video-2.2-baselines-dinamicos/
├── README.md             ← Este arquivo
└── dynamic_baseline.py   ← Baseline dinâmico com EMA e bandas de confiança
```

## ▶️ Como executar

```bash
python3 aula-02-deteccao-de-anomalias/video-2.2-baselines-dinamicos/dynamic_baseline.py
```
