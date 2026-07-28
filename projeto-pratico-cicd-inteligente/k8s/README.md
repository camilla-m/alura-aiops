# PATH B — Argo Rollouts real em cluster local

Aqui você roda o **Argo Rollouts de verdade** em um cluster `kind` (ou
`minikube`) e vê a mesma promoção/rollback automático do PATH A, só que nativa
no Kubernetes. O `canary_controller.py` do PATH A é a versão didática desta
mesma lógica.

## Pré-requisitos

- Docker
- [`kind`](https://kind.sigs.k8s.io/) **ou** [`minikube`](https://minikube.sigs.k8s.io/)
- `kubectl`
- Plugin [`kubectl argo rollouts`](https://argo-rollouts.readthedocs.io/en/stable/installation/#kubectl-plugin-installation)

## 1. Suba o cluster e construa a imagem do app

```bash
# cria o cluster local
kind create cluster --name cicd-lab

# constrói a imagem do checkout-service (a partir de ../app)
docker build -t checkout-service:latest ../app

# disponibiliza a imagem dentro do kind (sem registry)
kind load docker-image checkout-service:latest --name cicd-lab
# minikube: use `eval $(minikube docker-env)` ANTES do build, ou `minikube image load`
```

## 2. Instale o controlador do Argo Rollouts

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl -n argo-rollouts rollout status deploy/argo-rollouts
```

## 3. Aplique o lab (Prometheus, flagd, services, analysis, rollout)

```bash
kubectl apply -f prometheus.yaml
kubectl apply -f flagd.yaml
kubectl apply -f service.yaml
kubectl apply -f analysis-template.yaml
kubectl apply -f rollout.yaml
```

Neste primeiro apply o Rollout sobe direto para 100% (o Argo NÃO roda análise
na primeira revisão — não há baseline a comparar). Isso é o seu **stable v1
saudável**.

```bash
kubectl argo rollouts get rollout checkout --watch
```

## 4. Dispare um canary RUIM e assista ao rollback automático

Troque o pod para o build `v2` doente (alta taxa de erro + latência):

```bash
kubectl argo rollouts set image checkout checkout=checkout-service:latest    # mantém a imagem
# como a imagem é a mesma, mude o COMPORTAMENTO via env:
kubectl patch rollout checkout --type=json -p='[
  {"op":"replace","path":"/spec/template/spec/containers/0/env/0/value","value":"v2"},
  {"op":"replace","path":"/spec/template/spec/containers/0/env/1/value","value":"0.35"},
  {"op":"replace","path":"/spec/template/spec/containers/0/env/2/value","value":"400"}
]'
```

Agora acompanhe:

```bash
kubectl argo rollouts get rollout checkout --watch
```

Você vai ver: `setWeight 10%` → `Paused` → `Analysis Running` →
`Analysis Failed` → **`Degraded` / rollback automático** para o v1. O Argo
aborta sozinho porque a `AnalysisTemplate` reprovou (success rate < 95% e/ou
p95 > 0.5s).

> Precisa de tráfego para gerar métricas. Rode um gerador dentro do cluster:
> ```bash
> kubectl run loadgen --image=curlimages/curl --restart=Never -- \
>   /bin/sh -c 'while true; do curl -s -X POST http://checkout-canary/checkout >/dev/null; sleep 0.1; done'
> ```

## 5. Agora um canary SAUDÁVEL e assista à promoção automática

```bash
kubectl patch rollout checkout --type=json -p='[
  {"op":"replace","path":"/spec/template/spec/containers/0/env/1/value","value":"0.0"},
  {"op":"replace","path":"/spec/template/spec/containers/0/env/2/value","value":"0"}
]'
kubectl argo rollouts get rollout checkout --watch
```

Todos os gates passam → o Rollout avança 10% → 25% → 50% → 100% e **promove**
sozinho.

## Comandos úteis

```bash
kubectl argo rollouts get rollout checkout --watch   # timeline visual
kubectl argo rollouts promote checkout               # promoção manual
kubectl argo rollouts abort checkout                 # rollback manual
kubectl argo rollouts dashboard                       # UI web em :3100
```

## Limpeza

```bash
kind delete cluster --name cicd-lab
```

## Nota sobre o Prometheus (pasta `prometheus.yaml`)

O `prometheus.yaml` deste diretório sobe um Prometheus mínimo que descobre os
pods do `checkout` pelas annotations `prometheus.io/scrape`. É só o necessário
para a `AnalysisTemplate` conseguir consultar as métricas. Em produção você
usaria o kube-prometheus-stack / Prometheus Operator.
