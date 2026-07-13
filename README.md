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

### Projeto Prático Final: Laboratório com Ferramentas Reais

Para coroar o aprendizado, o repositório inclui um projeto prático que coloca os alunos de frente com uma infraestrutura real:

```
projeto-pratico-aiops/              # Laboratório end-to-end
├── docker-compose.yml              # Prometheus, Grafana, Jaeger, FastAPI
├── app/                            # API com OpenTelemetry e endpoint de caos
├── grafana/                        # Dashboards RED Method pré-configurados
└── ai_troubleshooter.py            # Script AIOps consumindo a API do Prometheus
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
| **Lab** | Projeto | Laboratório Prático End-to-End com Docker Compose |

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
