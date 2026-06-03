# Vídeo 1.4 — Observabilidade operacional em ambientes distribuídos

## 🎬 Roteiro

**Tipo:** Explicar Teoria  
**Habilidade:** Mapear a interconectividade e dependências operacionais durante o troubleshooting de falhas complexas.

### Desenvolvimento

- **Teoria:** Como as verticais de observabilidade se conectam em tempo real

---

## 💡 Conceitos-chave

- **Three pillars of observability:** Logs, Métricas e Traces — cada um com seu papel
- **Service mesh topology:** Como o mapa de dependências orienta o troubleshooting
- **Context propagation:** Como um trace_id atravessa múltiplos serviços
- **Correlation IDs:** Rastreabilidade fim a fim de uma requisição

---

## 📂 Arquivos deste vídeo

```
video-1.4-observabilidade/
├── README.md                       ← Este arquivo
├── observability_topology.py       ← Mapa de dependências e trace propagation
└── docker-compose.yml              ← Stack de observabilidade local (Prometheus + Grafana + Loki)
```
