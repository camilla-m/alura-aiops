# Vídeo 5.1 — Datadog, PagerDuty e observabilidade inteligente

## 🎬 Roteiro

**Tipo:** Apresentar Contexto  
**Habilidade:** Entender as capacidades nativas de AIOps das principais plataformas de observabilidade do mercado.

### Desenvolvimento

1. **Panorama:** Posicionar Datadog e PagerDuty no ecossistema de AIOps
2. **Datadog Watchdog:** Como a IA nativa detecta anomalias sem configuração manual
3. **PagerDuty AIOps:** Event intelligence e supressão inteligente de alertas
4. **Demo:** Executar `platform_integration.py` e ver a arquitetura de integração simulada

---

## 💡 Conceitos-chave

- **Observability platform:** Plataforma unificada que agrega métricas, logs e traces com IA integrada
- **Datadog Watchdog:** Motor de IA do Datadog que detecta anomalias proativamente sem threshold
- **PagerDuty Event Intelligence:** Correlação e supressão automática de alertas no fluxo de on-call
- **API-first integration:** Integrar plataformas via API para automação de incidentes
- **On-call routing:** Direcionar alertas para a pessoa certa no momento certo automaticamente

---

## 📂 Arquivos deste vídeo

```
video-5.1-datadog-pagerduty/
├── README.md                  ← Este arquivo
└── platform_integration.py    ← Demonstração da arquitetura de integração Datadog + PagerDuty
```

## ▶️ Como executar

```bash
python3 aula-05-operacoes-resilientes/video-5.1-datadog-pagerduty/platform_integration.py
```
