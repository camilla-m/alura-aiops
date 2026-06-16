# Vídeo 5.2 — Fluxos integrados de AIOps

## 🎬 Roteiro

**Tipo:** Mostrar Solução  
**Habilidade:** Conectar todos os módulos de AIOps em um pipeline operacional unificado e event-driven.

### Desenvolvimento

1. **Visão sistêmica:** Como os módulos das aulas anteriores se conectam em um fluxo real
2. **Event-driven pipeline:** Cada evento dispara o próximo passo automaticamente
3. **Observability → Action:** Do sinal bruto à resolução sem intervenção manual
4. **Demo:** Executar `unified_pipeline.py` e ver o fluxo completo do alerta à documentação

---

## 💡 Conceitos-chave

- **Unified pipeline:** Fluxo único que conecta detecção, correlação, diagnóstico e remediação
- **Event-driven architecture:** Cada etapa é disparada por eventos, não por polling ou cron jobs
- **Signal-to-resolution:** Métrica que mede o tempo do primeiro sinal à resolução completa
- **Pipeline orchestration:** Coordenar a execução ordenada e condicional de múltiplos módulos
- **Feedback loop:** Resultado de remediações alimentando os modelos de detecção para melhorar com o tempo

---

## 📂 Arquivos deste vídeo

```
video-5.2-fluxos-integrados/
├── README.md              ← Este arquivo
└── unified_pipeline.py    ← Pipeline unificado do sinal à resolução e documentação
```

## ▶️ Como executar

```bash
python3 aula-05-operacoes-resilientes/video-5.2-fluxos-integrados/unified_pipeline.py
```
