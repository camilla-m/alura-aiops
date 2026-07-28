# Feature Flags — flagd / OpenFeature (o "LaunchDarkly open source")

Este lab usa **feature flags** para separar **deploy** de **release**, um dos
pilares do Curso 4. O código novo pode estar em produção (deploy do canary v2)
enquanto o comportamento novo fica desligado por trás de uma flag, e é ligado
(release) de forma gradual e reversível.

## Por que flagd e não LaunchDarkly?

O curso cita o **LaunchDarkly** como a referência de mercado em feature
management. Para o lab rodar 100% local, offline e sem cadastro, usamos o
**flagd**, o engine open source do projeto **OpenFeature** (padrão CNCF de
feature flags). Os conceitos são os mesmos e o código do app fala com os dois
pela mesma API de avaliação — trocar de um para o outro é trocar o *provider*.

| Conceito | LaunchDarkly | flagd / OpenFeature (este lab) |
|---|---|---|
| Serviço que guarda e avalia as flags | LaunchDarkly SaaS | `flagd` (container local) |
| Definição das flags | UI/API do LaunchDarkly | `flags.flagd.json` (arquivo neste diretório) |
| Flag booleana | Boolean flag | `variants: {on:true, off:false}` |
| Rollout percentual | Percentage rollout | operador `fractional` |
| Kill switch | Toggle off | flag booleana `kill-switch` |
| Segmentação por usuário/contexto | Targeting rules | operador `targeting` (contexto OFREP) |
| SDK no app | `launchdarkly-server-sdk` | OpenFeature SDK / chamada OFREP direta |

## As flags deste lab (`flags.flagd.json`)

| Flag | Tipo | Default | Papel no lab |
|---|---|---|---|
| `new-checkout-flow` | boolean | `off` | Liga o fluxo de checkout novo (v2). É o **release** desacoplado do deploy. Com ela `off`, o canary v2 se comporta igual ao stable; com ela `on`, o build v2 passa a aplicar `ERROR_RATE`/`EXTRA_LATENCY_MS`. |
| `checkout-canary-rollout` | boolean + `fractional` | 10% `on` | Rollout percentual: libera o recurso para ~10% das avaliações (bucketing pelo `targetingKey`). Suba os 10 para 25/50/100 para simular o avanço gradual. |
| `kill-switch` | boolean | `off` | Corta o `/checkout` instantaneamente (HTTP 503), sem redeploy. É a rede de segurança do release. |

## Como o app consome as flags

O `app/main.py` avalia as flags via **OFREP** (OpenFeature Remote Evaluation
Protocol), a API REST do flagd na porta **8016**:

```
POST http://flagd:8016/ofrep/v1/evaluate/flags/kill-switch
{ "context": { "targetingKey": "<id-aleatorio-por-request>" } }
--> { "key": "kill-switch", "value": false, "reason": "STATIC", "variant": "off" }
```

O `targetingKey` aleatório por requisição é o que faz o operador `fractional`
distribuir o rollout percentual entre as chamadas. Se o flagd estiver fora do
ar, o app cai no valor `default` seguro (nunca derruba a request).

## Experimente (com o `docker compose up` no ar)

```bash
# ver como cada versão enxerga as flags
curl -s http://localhost:8001/flags   # stable v1
curl -s http://localhost:8002/flags   # canary v2

# ligar o fluxo novo: edite flags.flagd.json -> "new-checkout-flow".defaultVariant: "on"
# o flagd recarrega o arquivo automaticamente (hot reload).

# acionar o kill-switch: edite "kill-switch".defaultVariant: "on"
curl -s -X POST http://localhost:8002/checkout   # passa a responder 503
```
