# Vídeo 2.1 — Progressive delivery: canary, blue-green e feature flags

## 🎬 Roteiro

**Tipo:** Apresentar Contexto  
**Habilidade:** Reconhecer que a escolha da estratégia de release é, no fundo, uma escolha de blast radius: quantos usuários você aceita atingir se a versão nova estiver quebrada.

### Desenvolvimento

1. **Cenário real:** Uma mesma versão nova precisa ir para 100 mil usuários — de quantas formas dá para fazer isso?
2. **Teoria:** Canary, blue-green e feature flags lado a lado; exposição ao longo do tempo e blast radius

---

## 💡 Conceitos-chave

- **Progressive delivery:** Expor a mudança de forma gradual e reversível em vez de tudo de uma vez
- **Canary:** Sobe o peso da versão nova em degraus (5% → 20% → 50% → 100%) com pausas para observar
- **Blue-green:** Dois ambientes idênticos; cutover instantâneo 0% → 100% e o antigo fica como rollback
- **Feature flag:** Código já em produção, ligado por coorte/atributo sem redeploy
- **Blast radius:** Fração de usuários atingidos se a versão nova falhar naquele instante

---

## 📂 Arquivos deste vídeo

```
video-2.1-progressive-delivery-revisao/
├── README.md                ← Este arquivo
└── delivery_strategies.py   ← Simula os 3 rollouts e compara blast radius
```

## ▶️ Como executar

```bash
python3 curso4-aula-02-progressive-delivery/video-2.1-progressive-delivery-revisao/delivery_strategies.py
```
