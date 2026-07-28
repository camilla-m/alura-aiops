# 🚦 Projeto Prático 2 — Argo Rollouts em Kubernetes (Curso 4)

> **Carreira:** AIOps
> **Curso:** Curso 4 — CI/CD Inteligente (Deploys progressivos, canary e feature flags)
> **Instrutora:** Camilla Martins

Laboratório **hands-on** que roda um **canary deployment com o Argo Rollouts de
verdade** em um cluster Kubernetes local (`kind` ou `minikube`). Você vê a mesma
promoção e rollback automáticos do [Projeto Prático 1](../projeto-pratico-cicd-canary-local/),
só que agora nativos no Kubernetes: o roteamento por peso é real e a decisão dos
gates fica a cargo de uma `AnalysisTemplate` consultando o Prometheus.

A ideia central continua a mesma:

> **Deploy não é Release.** O Argo Rollouts coloca o build novo em produção de
> forma progressiva (canary) e só o promove se as **métricas reais** aprovarem
> cada gate. Se degradar, ele faz **rollback sozinho** — sem intervenção humana.

Este é o **segundo dos dois labs** de entrega progressiva do curso. No primeiro,
a lógica dos gates era um script Python didático (`canary_controller.py`); aqui
ela roda no controlador real do Argo Rollouts.

---

## 🎯 Objetivo

- Instalar o **Argo Rollouts** em um cluster local e rodar um `Rollout` com
  estratégia **canary** (`setWeight 10 → 25 → 50 → 100`).
- Escrever os gates como uma **`AnalysisTemplate`** que consulta o Prometheus
  (success rate e latência p95) e reprova o canary quando ele degrada.
- Disparar um canary **ruim** e assistir ao **rollback automático** via
  `AnalysisRun`, e um canary **bom** para ver a **promoção automática**.
- Enxergar o roteamento de tráfego **real** por peso (via replica count), não uma
  simulação.

---

## 🏗️ Arquitetura

```
                    ┌─────────────────────────────────────────────┐
                    │              Argo Rollouts controller        │
                    │   (setWeight · pause · analysis · rollback)  │
                    └───────────────┬─────────────────┬───────────┘
                                    │ observa/decide   │ dispara
                                    │                  ▼
                                    │        ┌───────────────────────┐
                                    │        │   AnalysisRun (gate)   │
                                    │        │ successCondition/       │
                                    │        │ failureLimit sobre      │
                                    │        │ Prometheus              │
                                    │        └───────────┬────────────┘
                                    │                    │ PromQL
                                    ▼                    ▼
   ┌──────────────────┐   ┌──────────────────┐   ┌────────────────────┐
   │  checkout-stable │   │  checkout-canary │   │     Prometheus      │
   │   (Service)      │   │   (Service)      │   │  (scrape por pod    │
   └────────┬─────────┘   └────────┬─────────┘   │   annotations)      │
            │                      │             └─────────▲──────────┘
            ▼                      ▼                       │ /metrics
      ┌──────────────────────────────────────┐            │
      │        Rollout: checkout (5 pods)     │────────────┘
      │  stable vs canary por pod-template-hash│
      │  env: APP_VERSION / ERROR_RATE / …     │
      └───────────────────┬────────────────────┘
                          │ OFREP :8016
                          ▼
                    ┌───────────┐
                    │   flagd   │  new-checkout-flow · canary-rollout · kill-switch
                    └───────────┘
```

Os `Service` `checkout-stable` e `checkout-canary` recebem o selector de
`pod-template-hash` que o Argo injeta, e é assim que o tráfego é fatiado de
verdade conforme o `setWeight`.

---

## 🛠️ Pré-requisitos

- **Docker**
- [`kind`](https://kind.sigs.k8s.io/) **ou** [`minikube`](https://minikube.sigs.k8s.io/) (cluster Kubernetes local)
- [`kubectl`](https://kubernetes.io/docs/tasks/tools/)
- Plugin [`kubectl argo rollouts`](https://argo-rollouts.readthedocs.io/en/stable/installation/#kubectl-plugin-installation)

---

## 🧪 Passo a passo

### 1. Suba o cluster e construa a imagem do app

```bash
# cria o cluster local
kind create cluster --name cicd-lab

# constrói a imagem do checkout-service (contexto ./app, na raiz deste projeto)
docker build -t checkout-service:latest ./app

# disponibiliza a imagem dentro do kind (sem registry)
kind load docker-image checkout-service:latest --name cicd-lab
# minikube: use `eval $(minikube docker-env)` ANTES do build, ou `minikube image load`
```

### 2. Instale o controlador do Argo Rollouts

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl -n argo-rollouts rollout status deploy/argo-rollouts
```

### 3. Aplique o lab (Prometheus, flagd, services, analysis, rollout)

Os manifestos estão na **raiz deste projeto** (não há mais subpasta `k8s/`):

```bash
kubectl apply -f prometheus.yaml
kubectl apply -f flagd.yaml
kubectl apply -f service.yaml
kubectl apply -f analysis-template.yaml
kubectl apply -f rollout.yaml
```

Neste primeiro apply o Rollout sobe direto para 100% (o Argo **não** roda
análise na primeira revisão — não há baseline a comparar). Isso é o seu
**stable v1 saudável**.

```bash
kubectl argo rollouts get rollout checkout --watch
```

> **Gere tráfego** para o canary ter métricas — sem isso a `AnalysisTemplate`
> não tem o que medir. Rode um gerador dentro do cluster:
> ```bash
> kubectl run loadgen --image=curlimages/curl --restart=Never -- \
>   /bin/sh -c 'while true; do curl -s -X POST http://checkout-canary/checkout >/dev/null; sleep 0.1; done'
> ```

### 4. Dispare um canary RUIM e assista ao rollback automático

A imagem é a mesma; o que muda é o **comportamento** via env. Patch o Rollout
para o build `v2` doente (alta taxa de erro + latência):

```bash
kubectl patch rollout checkout --type=json -p='[
  {"op":"replace","path":"/spec/template/spec/containers/0/env/0/value","value":"v2"},
  {"op":"replace","path":"/spec/template/spec/containers/0/env/1/value","value":"0.35"},
  {"op":"replace","path":"/spec/template/spec/containers/0/env/2/value","value":"400"}
]'
kubectl argo rollouts get rollout checkout --watch
```

Você vai ver: `setWeight 10%` → `Paused` → `Analysis Running` →
`Analysis Failed` → **`Degraded` / rollback automático** para o v1. O Argo aborta
sozinho porque a `AnalysisTemplate` reprovou (success rate < 95% e/ou p95 > 0.5s).

### 5. Agora um canary SAUDÁVEL e assista à promoção automática

```bash
kubectl patch rollout checkout --type=json -p='[
  {"op":"replace","path":"/spec/template/spec/containers/0/env/1/value","value":"0.0"},
  {"op":"replace","path":"/spec/template/spec/containers/0/env/2/value","value":"0"}
]'
kubectl argo rollouts get rollout checkout --watch
```

Todos os gates passam → o Rollout avança 10% → 25% → 50% → 100% e **promove**
sozinho.

### Comandos úteis

```bash
kubectl argo rollouts get rollout checkout --watch   # timeline visual
kubectl argo rollouts promote checkout               # promoção manual
kubectl argo rollouts abort checkout                 # rollback manual
kubectl argo rollouts dashboard                      # UI web em :3100
```

### 6. Limpeza

```bash
kubectl delete pod loadgen --ignore-not-found
kubectl delete -f rollout.yaml -f analysis-template.yaml -f service.yaml -f flagd.yaml -f prometheus.yaml
kind delete cluster --name cicd-lab
```

---

## 🧩 Como a AnalysisTemplate funciona

O arquivo `analysis-template.yaml` define os **gates automáticos** do canary. É
exatamente a lógica que o `canary_controller.py` do [Projeto Prático 1](../projeto-pratico-cicd-canary-local/)
reproduz no host, só que aqui nativa no Argo Rollouts.

Cada métrica é medida em janela (`interval`) por um número de vezes (`count`) e
tem um `successCondition`. Se o número de medições que violam a condição atingir
o `failureLimit`, a análise **reprova** e o Rollout aborta:

| Gate | Query (PromQL) | successCondition |
|---|---|---|
| **success-rate** | `sum(rate(http_requests_total{version="v2",status=~"2.."}[1m])) / sum(rate(http_requests_total{version="v2"}[1m]))` | `result >= 0.95` |
| **p95-latency** | `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{version="v2"}[1m])) by (le))` | `result <= 0.5` |

Ambos usam `interval: 20s`, `count: 4` e `failureLimit: 2` — ou seja, medem 4
vezes e reprovam se 2 medições violarem a condição. O `rollout.yaml` referencia
essa template em cada passo (`setWeight` → `pause` → `analysis`), de modo que
todo avanço de peso passa pelo gate antes de continuar.

O app (`app/main.py`) expõe `http_requests_total{version,status}` e
`http_request_duration_seconds{version}`, e o `prometheus.yaml` descobre os pods
do `checkout` pelas annotations `prometheus.io/scrape` — fechando o ciclo
métricas → análise → decisão.

---

## 🚫 O que este lab NÃO faz

- **Não substitui um pipeline de CI.** Não há build/test/registry automatizado
  aqui; o foco é a etapa de **entrega progressiva** (CD) e a análise automática.
- **Não é setup de produção.** O Prometheus é mínimo (descobre pods por
  annotation, sem persistência nem HA); em produção você usaria o
  kube-prometheus-stack / Prometheus Operator. flagd e o resto rodam sem
  autenticação, TLS ou HA — são para aprendizado local.
- **Não usa traffic routing por service mesh.** O canary é fatiado por
  **replica count** (o modo padrão do Argo Rollouts). Para roteamento por peso
  fino (ex.: 7% exatos) você plugaria um provider de tráfego (Istio, NGINX, ALB,
  SMI) na estratégia canary.
- **Não usa LaunchDarkly de verdade.** Usa o `flagd` (OpenFeature), o
  equivalente open source, servido por um `ConfigMap` (`flagd.yaml`). As flags
  espelham as do [Projeto Prático 1](../projeto-pratico-cicd-canary-local/)
  (`flags/flags.flagd.json`).
- **Não faz análise estatística avançada** (Mann-Whitney, etc.). Os gates são
  por limiares (success rate e p95 absoluto), suficientes para ilustrar a
  mecânica da `AnalysisTemplate`.

---

## 📁 Estrutura

```
projeto-pratico-cicd-argo-rollouts/
├── README.md                       # este arquivo
├── rollout.yaml                    # Rollout canary (setWeight 10→25→50→100 + análise)
├── analysis-template.yaml          # gates: success rate >= 95% e p95 <= 0.5s
├── service.yaml                    # services checkout-stable e checkout-canary
├── prometheus.yaml                 # Prometheus mínimo (scrape por pod annotations)
├── flagd.yaml                      # flagd via ConfigMap (OFREP :8016 / gRPC :8013)
├── flags/
│   └── flags.flagd.json            # flags do flagd (espelham o flagd.yaml)
└── app/
    ├── main.py                     # checkout-service (FastAPI + prometheus-client + OFREP)
    ├── Dockerfile
    └── requirements.txt
```

---

⬅️ **Lab anterior:** [`../projeto-pratico-cicd-canary-local/`](../projeto-pratico-cicd-canary-local/) —
a mesma promoção/rollback automático **sem Kubernetes**, com `docker compose` e
um controlador de canary em Python (bom para entender a mecânica antes de trazer
o Argo Rollouts para o cluster).

---

> ⚠️ **Nota:** este projeto contempla conteúdos técnicos com maior nível de
> detalhamento, para garantir que o estudante compreenda o racional por trás de
> cada tópico e consiga aplicar o conhecimento com autonomia e pensamento
> crítico.
