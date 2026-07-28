# Vídeo 5.3 — LaunchDarkly: feature flags com targeting e rollout

## 🎬 Roteiro

**Tipo:** Apresentar Solução  
**Habilidade:** Implementar um mini feature-flag engine no estilo LaunchDarkly — flags com targeting rules por atributo de usuário, percentage rollout determinístico por hash da userKey e kill switch — e explicar o mapeamento com os conceitos reais.

### Desenvolvimento

1. **Cenário real:** O time quer liberar um recurso para 20% dos usuários do plano enterprise no Brasil, e poder desligar tudo em 1 clique
2. **Solução:** Um flag engine que avalia regras de targeting em ordem, faz bucketing determinístico por hash e respeita um kill switch global

---

## 💡 Conceitos-chave

- **Flag:** chave booleana/multivariada que controla comportamento em runtime, sem redeploy
- **Variation:** os valores possíveis que um flag pode servir (ex.: `true`/`false`, `control`/`treatment`)
- **Targeting rule:** condição sobre atributos do contexto (plano, país) que serve uma variation
- **Percentage rollout:** distribuição determinística por hash da userKey (o mesmo usuário sempre cai no mesmo bucket)
- **Kill switch:** desligar o targeting do flag serve a `off variation` para todos instantaneamente

---

## 📂 Arquivos deste vídeo

```
video-5.3-launchdarkly/
├── README.md           ← Este arquivo
└── feature_flags.py    ← Mini flag engine com targeting + rollout + kill switch
```

## ▶️ Como executar

```bash
python3 curso4-aula-05-ferramentas-praticas/video-5.3-launchdarkly/feature_flags.py
```
