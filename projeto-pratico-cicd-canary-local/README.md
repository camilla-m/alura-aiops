# 🚦 Projeto Prático 1 — Canary Local (Curso 4)

> **Carreira:** AIOps
> **Curso:** Curso 4 — CI/CD Inteligente (Deploys progressivos, canary e feature flags)
> **Instrutora:** Camilla Martins

Laboratório **hands-on** que reproduz um **canary deployment** com promoção e
rollback automáticos **sem precisar de Kubernetes**. Tudo roda **localmente** com
`docker compose` e um controlador em Python que faz o papel do Argo Rollouts.

A ideia central que o lab prova na prática:

> **Deploy não é Release.** Colocar o código novo em produção (deploy) é uma
> coisa; expor o comportamento novo aos usuários (release) é outra. Deploys
> progressivos (canary) + feature flags te dão controle e reversibilidade sobre
> as duas coisas, com decisão automática baseada em **métricas reais**.

Este é o **primeiro dos dois labs** de entrega progressiva do curso. Aqui a
lógica dos gates é didática e roda no host; no [lab seguinte](../projeto-pratico-cicd-argo-rollouts/)
você roda a mesma coisa com o **Argo Rollouts de verdade** em Kubernetes.

---

## 🎯 Objetivo

- Rodar um **canary deployment** onde o tráfego avança em passos (10% → 25% →
  50% → 100%) e cada passo é um **gate** que analisa métricas antes de seguir.
- Ver a **promoção automática** quando o canary está saudável e o **rollback
  automático** quando ele degrada — sem intervenção humana.
- Usar **feature flags** para separar deploy de release e ter um **kill-switch**
  que corta um recurso em milissegundos.

O ponto-chave: o `canary_controller.py` **não é um mock**. Ele consulta as
métricas **reais** do canary no Prometheus (success rate e latência p95) e decide
PROMOVER ou fazer ROLLBACK exatamente como uma `AnalysisTemplate` do Argo
Rollouts faria.

---

## 🏗️ Arquitetura

```
                        ┌─────────────────────────────────────────────┐
                        │                 loadgen.py                   │
                        │        (tráfego para stable + canary)        │
                        └───────────────┬──────────────┬──────────────┘
                                        │              │
                          POST /checkout│              │POST /checkout
                                        ▼              ▼
                        ┌──────────────────┐   ┌──────────────────┐
                        │ checkout-STABLE  │   │ checkout-CANARY  │
                        │   APP_VERSION=v1 │   │   APP_VERSION=v2 │
                        │   (saudável)     │   │   (buggy p/demo) │
                        └────────┬─────────┘   └────────┬─────────┘
                                 │  /metrics            │  /metrics
                                 │   (version=v1)       │   (version=v2)
                                 │                      │
             flags (OFREP :8016) │                      │ flags (OFREP :8016)
                    ┌────────────┴──────────────────────┴───────────┐
                    │                    flagd                       │
                    │  new-checkout-flow · canary-rollout · kill-sw  │
                    └────────────────────────────────────────────────┘
                                 │                      │
                                 ▼                      ▼
                        ┌─────────────────────────────────────────────┐
                        │                  Prometheus                  │
                        │      (raspa v1 e v2, guarda as séries RED)   │
                        └───────────┬────────────────────┬────────────┘
                                    │                    │
                    queries success │        dashboards  │
                    rate + p95      ▼                    ▼
              ┌──────────────────────────────┐   ┌────────────────────┐
              │      canary_controller.py     │   │      Grafana        │
              │  (o "Argo Rollouts" local)    │   │ (stable vs canary)  │
              │  setWeight 10→25→50→100        │   └────────────────────┘
              │  PROMOTE ✅  ou  ROLLBACK ↩️   │
              └──────────────────────────────┘
```

O `canary_controller.py` é a peça que, num cluster de verdade, seria o
controlador do Argo Rollouts. Ele lê o Prometheus, roda os gates e toma a
decisão. No [Projeto Prático 2](../projeto-pratico-cicd-argo-rollouts/) essa
peça vira o controlador real e a lógica dos gates vira uma `AnalysisTemplate`.

---

## 🛠️ Pré-requisitos

- **Docker** e **Docker Compose** (o `docker compose` moderno, plugin v2)
- **Python 3.10+** no host (para rodar `loadgen.py` e `canary_controller.py`)

Os scripts `canary_controller.py` e `loadgen.py` usam **apenas a biblioteca
padrão** do Python — nenhum `pip install` no host. As dependências do app
(FastAPI etc.) ficam dentro do container.

---

## 🔌 Portas

| Serviço | URL | Descrição |
|---|---|---|
| checkout-stable (v1) | http://localhost:8001 | Versão estável (baseline) |
| checkout-canary (v2) | http://localhost:8002 | Versão canário |
| Prometheus | http://localhost:9090 | Métricas RED por versão |
| Grafana | http://localhost:3000 | Dashboard stable vs canary (anônimo/admin) |
| flagd (OFREP/REST) | http://localhost:8016 | API de avaliação de flags |
| flagd (gRPC) | localhost:8013 | Sync/avaliação gRPC |

---

## 🧪 Passo a passo

### 1. Suba o ambiente (canary DOENTE por padrão)

```bash
docker compose up --build
```

Isso sobe stable (v1 saudável), canary (v2 com `ERROR_RATE=0.35` e
`EXTRA_LATENCY_MS=400`), Prometheus, Grafana e flagd. O canário nasce **doente**
de propósito, para o primeiro cenário demonstrar o rollback.

### 2. Gere tráfego (outro terminal)

Sem tráfego não há métricas para analisar. Rode o gerador:

```bash
python3 loadgen.py
# ou dentro do compose:  docker compose --profile loadgen up --build
```

### 3. Rode o controlador de canary (outro terminal) e veja o ROLLBACK

```bash
python3 canary_controller.py
```

Ele lê as métricas **reais** do canary no Prometheus e roda os gates
(`setWeight 10 → 25 → 50 → 100`). Como o canary está doente, a análise reprova
e você vê o **ROLLBACK automático**:

```
🚦 CANARY CONTROLLER — Argo Rollouts (modo local, sem Kubernetes)
[..] ➡️  setWeight 10%  — encaminhando 10% do tráfego para o canary
[..] ⏸️  pause + analysis ...
[..]    medição 1/4: 🔴 canary sr=64.8% p95=0.612s ... -> success 64.8% < 95%; p95 0.612s > teto 0.500s
[..]    medição 2/4: 🔴 canary sr=63.1% p95=0.598s ...
[..] ❌ ANÁLISE REPROVADA: 2 medição(ões) ruim(s) no peso 10% (limite 2)
[..] ↩️  ROLLBACK automático: setWeight 0% — 100% do tráfego volta para o stable.
RESULTADO: 🔴 ROLLBACK — o canary v2 foi descartado, produção segue no v1.
```

### 4. Agora veja a PROMOÇÃO automática

Suba com o canary **saudável** e rode o controlador de novo:

```bash
# pare o compose (Ctrl+C) e suba com o canary saudável:
CANARY_ERROR_RATE=0 CANARY_EXTRA_LATENCY_MS=0 docker compose up --build
# nos outros terminais:
python3 loadgen.py
python3 canary_controller.py
```

Todos os gates passam → `RESULTADO: 🟢 PROMOÇÃO — o canary v2 é agora a versão estável.`

### 5. Brinque com as métricas e as flags

- **Flip do `ERROR_RATE`:** derrube um canary saudável no meio do rollout
  reiniciando o container canary com `CANARY_ERROR_RATE=0.5` e rode o
  controlador de novo — ele reprova e faz rollback.
- **Ajuste os gates:** o controlador aceita flags como
  `--min-success 0.98`, `--max-p95 0.3` ou `--steps 20,50,100`. Veja
  `python3 canary_controller.py --help`.
- **Grafana:** abra http://localhost:3000 → dashboard *"CI/CD Inteligente -
  Canary"* e compare success rate e p95 de v1 vs v2 lado a lado.
- **Feature flags:** veja `flags/README.md`. Ligue `new-checkout-flow`, mude o
  percentual de `checkout-canary-rollout` ou acione o `kill-switch` editando
  `flags/flags.flagd.json` (o flagd recarrega sozinho).

---

## 🧩 Como o app funciona

`app/main.py` é o mesmo `checkout-service` para as duas versões. O
comportamento vem de:

| Variável de ambiente | Efeito |
|---|---|
| `APP_VERSION` | `v1` (stable) ou `v2` (canary). Vira o label `version` das métricas. |
| `ERROR_RATE` | Probabilidade de falha `[0.0–1.0]` (simula build ruim). |
| `EXTRA_LATENCY_MS` | Latência extra em ms (simula regressão de performance). |
| `FLAGD_OFREP_URL` | Endpoint OFREP do flagd. |

Endpoints: `GET /health`, `GET /metrics`, `GET /flags` (debug) e
`POST /checkout`. As métricas expostas são `http_requests_total{version,status}`
e `http_request_duration_seconds{version}` — exatamente os sinais que o Argo
Rollouts (e o `canary_controller.py`) usam para decidir.

**Deploy ≠ Release na prática:** o build v2 pode estar em produção (deploy)
enquanto o comportamento novo fica atrás da flag `new-checkout-flow`. Só quando
a flag liga (release) é que o `ERROR_RATE`/`EXTRA_LATENCY_MS` do v2 "vazam" para
os usuários — e o `kill-switch` corta tudo em milissegundos, sem redeploy.

---

## 🚫 O que este lab NÃO faz

- **Não roteia tráfego real por peso.** O `loadgen` bate nas duas versões
  continuamente; o `setWeight` é a *decisão de gate* baseada em métricas reais do
  canary, não um proxy (Envoy/Istio) fatiando pacotes. O roteamento de verdade
  por peso é o que você vê no [Projeto Prático 2](../projeto-pratico-cicd-argo-rollouts/).
- **Não substitui um pipeline de CI.** Não há build/test/registry aqui; o foco é
  a etapa de **entrega progressiva** (CD) e a análise automática.
- **Não é setup de produção.** O Prometheus/Grafana/flagd estão sem
  autenticação, sem TLS, sem persistência e com uma stack mínima — são para
  aprendizado local.
- **Não usa LaunchDarkly de verdade.** Usa o `flagd` (OpenFeature), o
  equivalente open source, para rodar offline e sem cadastro. O mapeamento de
  conceitos está em `flags/README.md`.
- **Não faz análise estatística avançada** (Mann-Whitney, etc.). A comparação é
  por limiares (success rate, p95 absoluto e p95 relativo ao stable), que é o
  suficiente para ilustrar a mecânica dos gates.

---

## 📁 Estrutura

```
projeto-pratico-cicd-canary-local/
├── README.md                       # este arquivo
├── docker-compose.yml              # stable, canary, prometheus, grafana, flagd, loadgen
├── canary_controller.py            # o "Argo Rollouts" local (gates + promote/rollback)
├── loadgen.py                      # gerador de tráfego (host)
├── app/
│   ├── main.py                     # checkout-service (FastAPI + prometheus-client + OFREP)
│   ├── Dockerfile
│   └── requirements.txt
├── prometheus/
│   └── prometheus.yml              # raspa stable e canary
├── grafana/
│   ├── dashboards/canary_dashboard.json
│   └── provisioning/               # datasource + provider de dashboards
└── flags/
    ├── flags.flagd.json            # flags do flagd/OpenFeature
    └── README.md                   # mapeamento LaunchDarkly ↔ flagd
```

---

➡️ **Próximo lab:** [`../projeto-pratico-cicd-argo-rollouts/`](../projeto-pratico-cicd-argo-rollouts/) —
a mesma promoção/rollback automático, agora com o **Argo Rollouts real** em um
cluster Kubernetes (`kind`/`minikube`).

---

> ⚠️ **Nota:** este projeto contempla conteúdos técnicos com maior nível de
> detalhamento, para garantir que o estudante compreenda o racional por trás de
> cada tópico e consiga aplicar o conhecimento com autonomia e pensamento
> crítico.
