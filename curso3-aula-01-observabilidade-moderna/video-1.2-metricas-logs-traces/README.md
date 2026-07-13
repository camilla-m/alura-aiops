# Vídeo 1.2 — Métricas, logs e traces no troubleshooting moderno

## 🎬 Roteiro

**Tipo:** Demonstrar Solução  
**Habilidade:** Correlacionar as três verticais clássicas da telemetria de forma integrada para acelerar a localização de falhas.

### Desenvolvimento

1. **Problema:** A perda de tempo ao saltar entre ferramentas isoladas
2. **Solução:** Navegação integrada de logs a traces

---

## 💡 Conceitos-chave

- **Métricas:** Dados numéricos agregados (contadores, gauges, histogramas)
- **Logs:** Registros textuais detalhados de eventos discretos
- **Traces:** Fluxo de uma requisição através de múltiplos serviços
- **Correlação:** Uso de trace_id e span_id para unificar as três verticais

---

## 📂 Arquivos deste vídeo

```
video-1.2-metricas-logs-traces/
├── README.md                  ← Este arquivo
└── telemetry_correlation.py   ← Correlação integrada de métricas, logs e traces
```

## ▶️ Como executar

```bash
python3 curso3-aula-01-observabilidade-moderna/video-1.2-metricas-logs-traces/telemetry_correlation.py
```
