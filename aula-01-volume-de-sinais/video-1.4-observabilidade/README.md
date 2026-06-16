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
├── docker-compose.yml              ← Stack local: Prometheus + Grafana + Loki
├── prometheus.yml                  ← Configuração de scrape do Prometheus
└── promtail-config.yml             ← Agente de coleta de logs para o Loki
```

## ▶️ Como executar

### 1. Subir a stack de observabilidade (Docker)

```bash
cd aula-01-volume-de-sinais/video-1.4-observabilidade
docker compose up -d
```

Serviços disponíveis após subir:

| Serviço | URL | Acesso |
|---------|-----|--------|
| **Grafana** | http://localhost:3000 | admin / aiops123 |
| **Prometheus** | http://localhost:9090 | — |
| **Node Exporter** | http://localhost:9100/metrics | — |
| **Loki** | http://localhost:3100/ready | — |

### 2. Rodar o simulador de topologia (Python)

```bash
# Da raiz do projeto:
python3 aula-01-volume-de-sinais/video-1.4-observabilidade/observability_topology.py
```

### 3. Parar a stack

```bash
docker compose down          # para os containers
docker compose down -v       # para + apaga os volumes (dados)
```
