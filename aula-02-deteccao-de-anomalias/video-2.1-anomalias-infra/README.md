# Vídeo 2.1 — Detectando comportamento anormal em infraestrutura

## 🎬 Roteiro

**Tipo:** Apresentar Contexto  
**Habilidade:** Diferenciar comportamento anormal de variações esperadas em métricas de infraestrutura.

### Desenvolvimento

1. **Cenário real:** Introduzir um servidor com CPU oscilando — quando é problema, quando é normal?
2. **Problema:** Mostrar como thresholds estáticos geram falsos positivos em horários de pico legítimos
3. **Demo:** Executar `anomaly_detector.py` e comparar os dois métodos lado a lado

---

## 💡 Conceitos-chave

- **Anomalia vs. variação normal:** Nem todo pico é um problema — contexto importa
- **Threshold estático:** Valor fixo de corte (ex: CPU > 85%) — simples, mas gera falsos positivos
- **Z-Score:** Mede desvio em relação à média histórica — detecta anomalias relativas ao comportamento esperado
- **False Positive:** Alerta disparado sem que haja um problema real
- **Janela deslizante:** Analisa os N pontos anteriores para calcular a média e desvio padrão dinâmicos

---

## 📂 Arquivos deste vídeo

```
video-2.1-anomalias-infra/
├── README.md            ← Este arquivo
└── anomaly_detector.py  ← Comparativo: threshold estático vs. Z-Score
```

## ▶️ Como executar

```bash
python3 aula-02-deteccao-de-anomalias/video-2.1-anomalias-infra/anomaly_detector.py
```
