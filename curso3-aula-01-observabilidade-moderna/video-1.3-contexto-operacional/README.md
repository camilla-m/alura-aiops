# Vídeo 1.3 — Observabilidade orientada por contexto operacional

## 🎬 Roteiro

**Tipo:** Apresentar Contexto  
**Habilidade:** Mapear relações explícitas entre alterações no ambiente (deploys, configurações) e mudanças imediatas na saúde do ecossistema.

### Desenvolvimento

1. **Contexto:** Uma falha disparada pós-release
2. **Teoria:** Conceito de metadados de contexto

---

## 💡 Conceitos-chave

- **Metadados de contexto:** Informações de deploy, config changes e feature flags agregadas à telemetria
- **Change correlation:** Associação temporal entre mudanças e degradações
- **Deploy markers:** Anotações em dashboards que marcam deploys para correlação visual

---

## 📂 Arquivos deste vídeo

```
video-1.3-contexto-operacional/
├── README.md               ← Este arquivo
└── operational_context.py   ← Correlação de deploys e alterações com saúde do sistema
```

## ▶️ Como executar

```bash
python3 curso3-aula-01-observabilidade-moderna/video-1.3-contexto-operacional/operational_context.py
```
