# Vídeo 3.3 — Correlacionando mudanças e incidentes

## 🎬 Roteiro

**Tipo:** Mostrar Solução  
**Habilidade:** Identificar automaticamente deploys e mudanças como possíveis causas de incidentes.

### Desenvolvimento

1. **Contexto:** "Funcionava antes do deploy" — como provar e quantificar essa suspeita?
2. **Change-incident correlation:** Cruzar o timeline de incidentes com o histórico de mudanças
3. **Scoring de causalidade:** Atribuir probabilidade de causa com base em proximidade temporal e serviços afetados
4. **Demo:** Executar `change_correlator.py` e ver a IA identificando o deploy causador

---

## 💡 Conceitos-chave

- **Change-incident correlation:** Cruzar eventos de mudança (deploys, configurações) com início de incidentes
- **Temporal proximity:** Quanto mais próximo o deploy do incidente, maior a probabilidade de causalidade
- **Blast radius:** Quais serviços downstream podem ser afetados por uma mudança upstream
- **Drift detection:** Identificar quando o comportamento do sistema muda após uma alteração
- **CMDB (Configuration Management Database):** Registro histórico de mudanças na infraestrutura

---

## 📂 Arquivos deste vídeo

```
video-3.3-mudancas-incidentes/
├── README.md               ← Este arquivo
└── change_correlator.py    ← Motor de correlação deploy-incidente com scoring de causalidade
```

## ▶️ Como executar

```bash
python3 aula-03-investigacao-assistida-ia/video-3.3-mudancas-incidentes/change_correlator.py
```
