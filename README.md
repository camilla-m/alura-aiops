# 🤖 AIOps & Observabilidade Inteligente

> **Carreira:** AIOps  
> **Nível:** Nível 1 — Fundamentos de AIOps & Observabilidade  
> **Instrutora:** Camilla Martins  

---

## 🎯 Sobre este Repositório

Repositório dos cursos da formação **AIOps** da Alura, cobrindo desde automação de incidentes até observabilidade inteligente com IA.

---

## 📚 Cursos Disponíveis

### Curso 2 — AIOps & Automação de Incidentes

Capacitar profissionais de infraestrutura e operações a mitigar o excesso de alertas, aplicar baselines dinâmicos, integrar IA no troubleshooting e estruturar remediação automatizada.

```
aula-01-volume-de-sinais/           # Operando com alto volume de sinais
aula-02-deteccao-de-anomalias/      # Detecção de anomalias em operações
aula-03-investigacao-assistida-ia/  # Investigação operacional assistida por IA
aula-04-automacao-e-resposta/       # Automação operacional e resposta a incidentes
aula-05-operacoes-resilientes/      # Operações resilientes em ambientes distribuídos
```

### Curso 3 — Observabilidade Inteligente

Compreender observabilidade moderna com OpenTelemetry, análise de tendências, alertas inteligentes, investigação com IA e operações centralizadas sob pressão.

```
curso3-aula-01-observabilidade-moderna/     # Observabilidade moderna e análise operacional
curso3-aula-02-tendencias-comportamento/    # Tendências e comportamento operacional
curso3-aula-03-alertas-inteligentes/        # Alertas inteligentes e redução de ruído
curso3-aula-04-investigacao-logs-ia/        # Investigação operacional e análise inteligente de logs
curso3-aula-05-operacoes-inteligentes/      # Operações orientadas por observabilidade inteligente
```

### Curso 4 — CI/CD Inteligente

Aplicar IA e ML ao ciclo de entrega: análise preditiva de risco de deploy, progressive delivery com canary analysis automatizada, test intelligence, pipelines auto-otimizáveis e as ferramentas reais do mercado (Argo Rollouts, LaunchDarkly, Harness, Buildkite).

```
curso4-aula-01-analise-risco-predeploy/     # Análise de risco pré-deploy com ML
curso4-aula-02-progressive-delivery/        # Progressive delivery + canary analysis (Argo Rollouts)
curso4-aula-03-test-intelligence/           # Test selection, flaky detection e test impact
curso4-aula-04-pipelines-auto-otimizaveis/  # Gargalos, paralelismo, cache e agentes de otimização
curso4-aula-05-ferramentas-praticas/        # Harness, Argo Rollouts, LaunchDarkly e Buildkite
```

### Projetos Práticos: Laboratórios com Ferramentas Reais

Para coroar o aprendizado, o repositório inclui projetos práticos que colocam os alunos de frente com uma infraestrutura real:

```
projeto-pratico-aiops/              # Lab AIOps end-to-end (Curso 2/3)
├── docker-compose.yml              # Prometheus, Grafana, Jaeger, FastAPI
├── app/                            # API com OpenTelemetry e endpoint de caos
├── grafana/                        # Dashboards RED Method pré-configurados
└── ai_troubleshooter.py            # Script AIOps consumindo a API do Prometheus

projeto-pratico-cicd-inteligente/   # Lab de CI/CD Inteligente (Curso 4)
├── docker-compose.yml              # stable(v1) + canary(v2) + Prometheus + Grafana + flagd
├── canary_controller.py            # Canary analysis local (lógica do Argo Rollouts sobre Prometheus)
├── flags/                          # Feature flags flagd/OpenFeature (estilo LaunchDarkly)
└── k8s/                            # Argo Rollouts real em kind/minikube (PATH B)
```

---

## 🗺️ Ementa

| Curso | Aula | Tema |
|-------|------|------|
| **Curso 2** | Aula 1 | Operando ambientes com alto volume de sinais |
| | Aula 2 | Detecção de anomalias em operações |
| | Aula 3 | Investigação operacional assistida por IA |
| | Aula 4 | Automação operacional e resposta a incidentes |
| | Aula 5 | Operações resilientes em ambientes distribuídos |
| **Curso 3** | Aula 1 | Observabilidade moderna e análise operacional |
| | Aula 2 | Tendências e comportamento operacional |
| | Aula 3 | Alertas inteligentes e redução de ruído |
| | Aula 4 | Investigação operacional e análise inteligente de logs |
| | Aula 5 | Operações orientadas por observabilidade inteligente |
| **Curso 4** | Aula 1 | Análise de risco pré-deploy |
| | Aula 2 | Progressive delivery assistido |
| | Aula 3 | Test intelligence |
| | Aula 4 | Pipelines auto-otimizáveis |
| | Aula 5 | Ferramentas na prática (Harness, Argo, LaunchDarkly, Buildkite) |
| **Lab** | Projeto | Laboratório AIOps End-to-End com Docker Compose |
| | Projeto | Laboratório CI/CD Inteligente: canary + Argo Rollouts + feature flags |

---

## 👥 Público-alvo

| Perfil | Motivação |
|--------|-----------|
| SREs e DevOps Engineers | Integrar IA no dia a dia de operações |
| Platform Engineers | Construir plataformas inteligentes com automação assistida |
| Cloud Engineers | Otimizar custos e infraestrutura com ML |
| Gestores de TI | Entender o potencial de AIOps para decisões estratégicas |
| DevSecOps | Aplicar IA na proteção de pipelines e runtime |

---

## 🛠️ Pré-requisitos

- Python 3.10+
- Docker & Docker Compose
- Conhecimento básico de Kubernetes
- Acesso a uma conta Datadog ou Grafana (gratuita)

## 📦 Instalação

```bash
# Clone o repositório
git clone <repo-url>
cd alura-aidevops

# Instale as dependências globais
pip install -r requirements.txt

# Execute qualquer script de aula
python3 curso3-aula-01-observabilidade-moderna/video-1.1-evolucao-observabilidade/observability_evolution.py
```

---

> ⚠️ **Nota:** Este projeto contempla conteúdos técnicos profundos com maior nível de detalhamento, para garantir que o estudante compreenda o racional por trás de cada tópico e consiga aplicar o conhecimento com autonomia e pensamento crítico.
