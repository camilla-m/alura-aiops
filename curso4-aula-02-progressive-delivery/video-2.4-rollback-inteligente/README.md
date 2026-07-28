# Vídeo 2.4 — Rollback inteligente: detectar degradação e reverter sozinho

## 🎬 Roteiro

**Tipo:** Apresentar Solução  
**Habilidade:** Implementar uma regra de rollback automático por janelas de métricas e quantificar o ganho em tempo de detecção e blast radius sobre o rollback manual.

### Desenvolvimento

1. **Cenário real:** Um bug que só aparece sob carga real, quando o canary já subiu para 50%
2. **Solução:** Monitorar janelas curtas, exigir N janelas ruins consecutivas e reverter automaticamente; comparar com o rollback manual

---

## 💡 Conceitos-chave

- **Janela deslizante:** Métricas avaliadas em blocos curtos (aqui, 30s) durante todo o rollout
- **N janelas consecutivas:** Exigir persistência da degradação evita reverter por um único spike
- **Rollback automático:** Dispara em segundos, com o canary ainda em peso baixo
- **Blast radius poupado:** Diferença de usuários impactados entre reverter cedo (auto) e tarde (manual)
- **Timeline:** O instante exato da reversão vira métrica de qualidade do processo

---

## 📂 Arquivos deste vídeo

```
video-2.4-rollback-inteligente/
├── README.md          ← Este arquivo
└── smart_rollback.py  ← Monitora janelas e compara rollback auto vs manual
```

## ▶️ Como executar

```bash
python3 curso4-aula-02-progressive-delivery/video-2.4-rollback-inteligente/smart_rollback.py
```
