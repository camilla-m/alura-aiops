# Vídeo 2.5 — Hands-on: rollout canário de ponta a ponta

## 🎬 Roteiro

**Tipo:** Prática (exercício final da aula)  
**Habilidade:** Integrar estratégia canária, canary analysis estatística e rollback automático num único rollout que se promove ou se reverte sozinho.

### Desenvolvimento

1. **Cenário real:** Um rollout canário completo do `mapi-api`, degrau a degrau
2. **Prática:** Para cada step de peso, gerar tráfego sintético, rodar a análise e decidir avançar ou abortar; fechar com relatório

---

## 💡 Conceitos-chave

- **Pipeline canário completo:** `5% → 20% → 50% → 100%`, com um gate de análise por degrau
- **Tráfego sintético:** Baseline e canary gerados a cada gate para alimentar os testes
- **Decisão automática:** z-test de proporção + Mann-Whitney definem PROMOTE/ROLLBACK sem humano no loop
- **Blast radius contido:** Se abortar, a versão ruim só chegou até o peso do gate que falhou
- **Relatório final:** Consolida gates aprovados, desfecho e blast radius

> Dica: no fim do arquivo, troque `executar(canary_saudavel=True)` para
> `False` e veja o rollout abortar num canary degradado.

---

## 📂 Arquivos deste vídeo

```
video-2.5-hands-on/
├── README.md                    ← Este arquivo
└── progressive_delivery_lab.py  ← Rollout canário automatizado de ponta a ponta
```

## ▶️ Como executar

```bash
python3 curso4-aula-02-progressive-delivery/video-2.5-hands-on/progressive_delivery_lab.py
```
