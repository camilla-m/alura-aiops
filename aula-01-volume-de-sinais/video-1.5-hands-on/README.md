# Vídeo 1.5 — Hands-on: Investigando incidentes com múltiplos sinais

## 🎬 Roteiro

**Tipo:** Demonstrar Solução (Hands-on)  
**Habilidade:** Executar análises conjuntas de eventos, logs e métricas em cenários de incidentes reais.

### Desenvolvimento

- **Prática:** Exercício simulando o isolamento de uma falha em ambiente produtivo

---

## 💡 O que você vai praticar

1. Receber um conjunto de logs, métricas e traces misturados
2. Usar o correlator de eventos para agrupar sinais
3. Calcular o impact score do incidente
4. Gerar um relatório de triagem completo
5. Propor a causa raiz e próximos passos

---

## 📂 Arquivos deste vídeo

```
video-1.5-hands-on/
├── README.md                  ← Este arquivo
├── incident_investigation.py  ← Exercício completo de investigação
└── scenario_data/
    ├── logs.json              ← Logs do incidente simulado
    └── metrics.json           ← Métricas do incidente simulado
```

## ▶️ Como executar

```bash
# Da raiz do projeto:
python3 aula-01-volume-de-sinais/video-1.5-hands-on/incident_investigation.py
```
