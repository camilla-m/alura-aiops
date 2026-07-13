# auth-service-connection-pool-recovery

## Contexto
Este runbook deve ser utilizado quando o monitoramento disparar um alerta devido à ocupação do connection pool do `auth-service` superior a 90% (`connection_pool_active > 90%`) ou quando a taxa de erro HTTP 503 do serviço ultrapassar 50% (`auth-service error_rate > 50%`). 

Os sintomas mais comuns incluem erros de indisponibilidade HTTP 503 no frontend, conexões com o PostgreSQL próximas ao limite configurado (geralmente > 90/100) e latência p99 do serviço superior a 5 segundos.

---

## Pré-requisitos
*   **Acesso e Ferramentas**:
    *   Ferramenta de linha de comando `kubectl` instalada e configurada com acesso ao cluster correspondente.
    *   Utilitário `psql` (PostgreSQL Client) para execução de consultas administrativas.
    *   Acesso de rede ao host do PostgreSQL ou permissão para executar comandos via pod administrativo/bastion no namespace `production`.
*   **Permissões**:
    *   Permissões de leitura/escrita no namespace `production` do Kubernetes.
    *   Credenciais de superusuário (`postgres` ou similar) do banco de dados para encerramento de conexões e alteração de parâmetros.

---

## Diagnóstico Rápido (< 5 min)

### 1. Verificar volume de conexões no PostgreSQL
Identifique se a contagem total de conexões está próxima ao limite máximo do servidor executando a query abaixo:
```sql
-- Executar via psql
SELECT count(*), state FROM pg_stat_activity GROUP BY state;
```
*Output esperado (indicação de saturação):*
```text
 count |        state        
-------+---------------------
    93 | active
     5 | idle in transaction
     2 | idle
(3 rows)
```
Se a contagem total estiver próxima de 100 (ou do limite máximo atual), as conexões estão saturadas.

### 2. Verificar a existência de queries ativas presas
Liste as queries que estão sendo executadas há mais de 5 segundos para identificar possíveis gargalos ou transações presas:
```sql
-- Executar via psql
SELECT pid, now() - query_start AS duration, query, state
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '5 seconds'
ORDER BY duration DESC;
```
*Output esperado:*
```text
 pid  |    duration     |                        query                        | state  
------+-----------------+-----------------------------------------------------+--------
 1402 | 00:02:15.340211 | SELECT * FROM sessions WHERE user_id = $1 FOR UPDATE| active
 1408 | 00:01:45.892019 | SELECT * FROM audit_logs ORDER BY created_at DESC   | active
```
Se houver queries ativas com alta duração, prossiga para a **Causa 1**.

### 3. Verificar o arquivo de configuração do PostgreSQL
Confirme qual o limite atual configurado para `max_connections`:
```sql
-- Executar via psql
SHOW max_connections;
```
*Output esperado:*
```text
 max_connections 
-----------------
 100
(1 row)
```
Se o limite for de 100 conexões e o tráfego atual de pods do `auth-service` for superior à capacidade operacional de conexões dividida pelas réplicas, prossiga para a **Causa 2**.

### 4. Verificar logs do auth-service buscando vazamentos (leak) de conexões
Consulte os logs recentes do `auth-service` para verificar se há indicação de falha de timeout de conexão ou vazamentos:
```bash
# Executar via terminal
kubectl logs -n production -l app=auth-service --tail=150 | grep -iE "leak|timeout|pool|postgres"
```
*Output esperado:*
```text
[WARN] Connection pool leak detected: connection active for 35000ms.
[ERROR] HikariPool-1 - Connection is not available, request timed out after 5000ms.
```
Se houver logs contínuos indicando leaks, prossiga para a **Causa 3**.

---

## Procedimentos de Remediação

### Causa 1: Queries travadas bloqueando conexões
Se o diagnóstico apontar transações presas ou lentas impedindo a liberação de conexões do pool.
*Tempo estimado: 3 minutos*

1.  **Derrubar sessões ativas presas**:
    [⚠️ ATENÇÃO: pg_terminate_backend encerra forçadamente a sessão do usuário. Isso causará um erro temporário na requisição correspondente, mas liberará a conexão imediatamente.]
    Execute o comando abaixo para terminar sessões que estejam executando queries por mais de 30 segundos (excluindo a sua própria conexão):
    ```sql
    -- Executar via psql
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE state = 'active'
      AND now() - query_start > interval '30 seconds'
      AND pid <> pg_backend_pid();
    ```
    *Output esperado:*
    ```text
     pg_terminate_backend 
    ----------------------
     t
     t
    (2 rows)
    ```

2.  **Verificar liberação**:
    Rode novamente a consulta de diagnóstico rápido das conexões ativas para garantir que o número de conexões ociosas ou presas diminuiu.

---

### Causa 2: max_connections configurado muito baixo
Se o limite de conexões atual do banco não comporta o número de réplicas e tamanho máximo do pool configurado nos pods do `auth-service`.
*Tempo estimado: 5 minutos*

1.  **Aumentar o limite de conexões no PostgreSQL**:
    [⚠️ ATENÇÃO: Aumentar o max_connections consome mais recursos de memória e CPU do servidor de banco. Monitore a saúde do banco logo em seguida.]
    Se você estiver utilizando um banco autogerenciado, altere a configuração diretamente no servidor:
    ```sql
    -- Executar via psql
    ALTER SYSTEM SET max_connections = 200;
    ```
    Para que essa alteração tenha efeito, o banco de dados geralmente precisa de um reinício. Em ambientes Kubernetes de staging/desenvolvimento, faça o reinício do StatefulSet do banco:
    ```bash
    # Executar via terminal
    kubectl rollout restart statefulset postgres-db -n production
    ```
    *Output esperado:*
    ```text
    statefulset.apps/postgres-db restarted
    ```
    *Nota:* Em ambientes de produção que utilizam serviços gerenciados de nuvem (AWS RDS, GCP Cloud SQL), altere o parâmetro `max_connections` correspondente no painel ou via CLI do provedor (Parameter Groups / Flags) e execute o reboot do banco de dados conforme recomendado pela console do provedor.

---

### Causa 3: Driver de conexão com bug de leak
Se o código do `auth-service` ou o driver de banco atualizado estiver travando conexões e o volume aumentar linearmente sem vazão.
*Tempo estimado: 4 minutos*

1.  **Executar Rolling Restart dos pods do auth-service**:
    Isso força o encerramento dos pods atuais, fazendo com que as conexões TCP antigas mantidas por eles com o banco de dados sejam fechadas de forma limpa.
    ```bash
    # Executar via terminal
    kubectl rollout restart deployment auth-service -n production
    ```
    *Output esperado:*
    ```text
    deployment.apps/auth-service restarted
    ```

2.  **Acompanhar a evolução do restart**:
    Monitore a implantação até que todas as réplicas novas estejam prontas:
    ```bash
    # Executar via terminal
    kubectl rollout status deployment auth-service -n production
    ```
    *Output esperado:*
    ```text
    Waiting for deployment "auth-service" rollout to finish: 1 old replicas are pending termination...
    deployment "auth-service" successfully rolled out
    ```

---

## Validação
1.  **Verificar a saúde do serviço**:
    Acesse o endpoint de health check do `auth-service` de dentro de um dos pods para garantir que ele responde com status HTTP 200:
    ```bash
    # Executar via terminal
    POD_NAME=$(kubectl get pods -n production -l app=auth-service -o jsonpath='{.items[0].metadata.name}')
    kubectl exec -it $POD_NAME -n production -- curl -I http://localhost:8080/health
    ```
    *Output esperado:*
    ```text
    HTTP/1.1 200 OK
    Content-Type: application/json
    
    { "status": "UP", "database": "CONNECTED" }
    ```

2.  **Validar ocupação das conexões no banco de dados**:
    Garanta que a ocupação voltou aos níveis normais de regime operacional (< 70%).

---

## Escalação
Se as ações de remediação não restaurarem a estabilidade do sistema em até 10 minutos após a execução:
1.  **Acione a equipe de DBA**: Entre em contato pelo canal `#db-ops-escalation` ou via PagerDuty (Bob / DBA de plantão) para avaliar locks persistentes, gargalos de I/O ou redimensionamento de recursos do servidor.
2.  **Acione o time de desenvolvimento (Time Auth)**: Entre em contato pelo canal `#team-auth` (Carol / Lead) para providenciar o rollback imediato do deploy para a versão estável anterior (`v2.3.0`):
    ```bash
    # Executar via terminal
    kubectl rollout undo deployment auth-service -n production
    ```
    *Output esperado:*
    ```text
    deployment.apps/auth-service rolled back
    ```

---

## Histórico de Mudanças
| Data | Autor | Alteração |
|------|-------|-----------|
| 2026-06-16 | Alice (SRE) | Criação do runbook operacional pós-incidente INC-2024-0603-001 |
