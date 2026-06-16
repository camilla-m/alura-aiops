# Vídeo 4.3 — IA no fluxo de comunicação de incidentes

## 🎬 Roteiro

**Tipo:** Mostrar Solução  
**Habilidade:** Automatizar comunicações de incidente (Slack, war room, status page) com geração de texto por IA.

### Desenvolvimento

1. **Problema:** Durante um incidente, comunicar para múltiplos canais consome tempo crítico
2. **Geração automática:** IA sintetizando o estado atual em mensagens claras para diferentes audiências
3. **Stakeholder mapping:** Cada audiência precisa de um nível diferente de detalhe técnico
4. **Demo:** Executar `incident_communicator.py` e ver geração automática de updates e post-mortem

---

## 💡 Conceitos-chave

- **Incident communication:** Manter stakeholders informados durante e após um incidente
- **Audience-aware messaging:** Adaptar o nível técnico da mensagem para cada audiência (dev, negócio, cliente)
- **War room update:** Atualização técnica em tempo real para o time de resposta
- **Status page:** Comunicação pública do estado dos serviços para usuários finais
- **Post-mortem automation:** Gerar automaticamente o rascunho do relatório pós-incidente

---

## 📂 Arquivos deste vídeo

```
video-4.3-ia-fluxo-incidentes/
├── README.md                  ← Este arquivo
└── incident_communicator.py   ← Geração automática de comunicações e post-mortem com IA
```

## ▶️ Como executar

```bash
python3 aula-04-automacao-e-resposta/video-4.3-ia-fluxo-incidentes/incident_communicator.py
```
