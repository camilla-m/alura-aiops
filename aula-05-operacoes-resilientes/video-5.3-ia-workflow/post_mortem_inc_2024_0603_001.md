# Post-Mortem: INC-2024-0603-001
## Frontend 503 — auth-service connection pool esgotado

### 1. Sumário Executivo
No dia 3 de junho de 2024, entre 09:02 e 09:20 UTC-3, nosso sistema passou por uma instabilidade crítica que impediu que os usuários realizassem login ou finalizassem compras, resultando em erros intermitentes de página indisponível (HTTP 503). O incidente durou 18 minutos, afetou aproximadamente 50.000 usuários ativos e gerou um impacto financeiro estimado em R$ 90.000,00 devido à interrupção do fluxo de vendas.

O problema foi desencadeado pelo deploy da versão `v2.3.1` do serviço de autenticação (`auth-service`). Essa atualização introduziu uma nova versão do driver de conexão com o banco de dados PostgreSQL que se comportou de maneira incompatível com a capacidade máxima de conexões configurada no banco (limite rígido de 100 conexões), gerando um esgotamento rápido de recursos.

A recuperação foi efetuada pela equipe técnica por meio do encerramento forçado das conexões presas, aumento temporário no limite do banco para 200 conexões e reinício escalonado (rolling restart) dos servidores do serviço de autenticação. Para evitar recorrências, o time trabalhará na adoção de um pooler de conexões externo (PgBouncer), testes automáticos de estresse no pipeline de deploy e refatoração do driver de banco de dados.

---

### 2. Impacto
*   **Quantitativo:**
    *   **Duração:** 18 minutos.
    *   **Usuários Impactados:** ~50.000 usuários únicos.
    *   **Perda Financeira:** R$ 90.000,00 (estimado com base na taxa média de conversão do checkout no horário).
    *   **Métricas de Erro:** A taxa de erro HTTP 503 no gateway alcançou um pico de 82%.
    *   **Conexões de Banco:** 100% de ocupação do limite de 100 conexões concorrentes no PostgreSQL.
*   **Qualitativo:**
    *   Impossibilidade de acesso e realização de login na plataforma.
    *   Falhas de finalização de pagamento no `payment-service`, pois o serviço não conseguia validar tokens de autenticação com o `auth-service`.
    *   Aumento de chamados de suporte e queixas nas redes sociais.

---

### 3. Timeline
*   **T+0min (09:02):** Conclusão do deploy da v2.3.1 do `auth-service` (registro de mudança CHG-001). Início imediato do pico de abertura de conexões.
*   **T+2min (09:04):** Disparo de alertas automáticos indicando alta latência no `frontend` e esgotamento do pool no `auth-service`. Alice (SRE) inicia a triagem do incidente.
*   **T+5min (09:07):** Alice identifica o deploy recente (CHG-001) como provável causa raiz e aciona Bob (DBA) e Carol (Lead).
*   **T+8min (09:10):** Bob acessa o banco e executa o encerramento de queries travadas via `pg_terminate_backend` para liberar conexões ociosas.
*   **T+10min (09:12):** O limite `max_connections` do PostgreSQL é alterado via console gerenciado de 100 para 200 para absorver a carga represada.
*   **T+12min (09:14):** Carol inicia um rolling restart do `auth-service` para forçar os contêineres a liberarem conexões antigas e iniciarem com o novo limite.
*   **T+15min (09:17):** Início da redução na taxa de erros do frontend (HTTP 503 < 5%) e estabilização do tempo de resposta.
*   **T+18min (09:20):** Taxa de erro geral cai para menos de 1%. Sistema operando com latência p99 normalizada. Incidente encerrado.

---

### 4. Causa Raiz
O deploy da versão v2.3.1 do `auth-service` atualizou a biblioteca do driver PostgreSQL. Essa versão do driver possuía um comportamento agressivo na inicialização, abrindo mais conexões do que o especificado no pool local por pod e apresentando um vazamento (leak) de conexões ativas. Com o banco de dados configurado estaticamente para aceitar no máximo 100 conexões (`max_connections=100`), o limite foi estourado na inicialização dos pods, bloqueando quaisquer novas requisições e gerando erros em cascata nos serviços dependentes (`api-gateway` e `payment-service`).

**Diagrama de Causalidade:**
```
[Deploy auth-service v2.3.1]
             │
             ▼
[Driver executa abertura agressiva e vazamento de conexões]
             │
             ▼
[Esgotamento de max_connections (100) no PostgreSQL]
             │
             ▼
[Falha de conexão & Timeouts de banco no auth-service]
             │
             ▼
[Erros 503 em cascata no api-gateway, frontend e payment-service]
```

---

### 5. Fatores Contribuintes
*   **Falta de teste de carga no pipeline de CI/CD**: A alteração crítica de driver não passou por simulação de carga concorrente antes de ser mesclada.
*   **max_connections subdimensionado**: O limite de 100 conexões não possuía margem para picos ou vazamentos repentinos causados por atualizações de dependências.
*   **Ausência de PgBouncer**: A arquitetura dependia apenas do pool interno de cada réplica do microsserviço, sem uma camada centralizada para gerenciar e multiplexar o pool de conexões com o PostgreSQL.
*   **Threshold estático nos alertas**: O sistema de monitoramento alertava apenas quando o limite absoluto era alcançado, em vez de disparar alertas preditivos baseados na taxa de crescimento rápido do uso de conexões.

---

### 6. Ações de Remediação
*   Identificação e correlação do incidente com a mudança CHG-001 (T+5min).
*   Liberação imediata de sessões presas no banco via `pg_terminate_backend` (T+8min).
*   Aumento emergencial da capacidade de conexões do PostgreSQL para 200 (T+10min).
*   Rolling restart preventivo dos pods do `auth-service` para estabilizar o comportamento do driver (T+12min).

---

### 7. Action Items Preventivos

| Ação | Responsável | Prazo | Prioridade |
| :--- | :--- | :--- | :--- |
| Configurar e homologar PgBouncer em ambiente de staging e produção | Bob (DBA) | 7 dias | Alta |
| Incluir etapa de teste de carga simulando concorrência no pipeline de CI/CD | Alice (SRE) | 10 dias | Média |
| Criar alerta preditivo (rate of change) para ocupação de pools de banco | Alice (SRE) | 5 dias | Alta |
| Corrigir/fazer rollback da versão do driver do PostgreSQL no auth-service | Carol (Lead) | 3 dias | Crítica |
| Avaliar o limite de conexões de todos os bancos de dados em produção | Bob (DBA) | 15 dias | Baixa |

---

### 8. Lições Aprendidas
*   Drivers de banco de dados e bibliotecas de conexão devem ser tratados com o mesmo nível de rigor e teste que alterações diretas no código de negócio.
*   Depender exclusivamente de pools de conexão internos distribuídos em múltiplos pods pode sobrecarregar rapidamente o banco de dados principal. Um pooler centralizado de conexões é essencial para a resiliência operacional da arquitetura de microsserviços.
*   Alertas estáticos (ex: > 90%) não dão tempo de reação hábil sob condições de degradação rápida. Precisamos evoluir nossas métricas de alerta para modelos baseados em anomalias ou taxas de variação.
*   A rápida triagem do deploy CHG-001 como ponto inicial do incidente destaca o valor da integração de logs de eventos de CI/CD com a plataforma de monitoramento.

---

### 9. Métricas do Incidente
*   **MTTA (Tempo Médio de Detecção/Reconhecimento):** 2 minutos (09:02 a 09:04).
*   **MTTR (Tempo Médio de Resolução):** 18 minutos (09:02 a 09:20).
*   **SLO Burn:** Consumo de 12% do budget de erro trimestral de disponibilidade do frontend.
*   **Usuários Impactados:** ~50.000 usuários afetados.
