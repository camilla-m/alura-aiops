# Vídeo 4.2 — Runbooks como código

## 🎬 Roteiro

**Tipo:** Mostrar Solução  
**Habilidade:** Implementar runbooks operacionais como código versionável com auditoria e rollback.

### Desenvolvimento

1. **Problema:** Runbooks em wikis ficam desatualizados e não são auditáveis
2. **Runbook-as-Code:** Definir procedimentos como estruturas de dados executáveis
3. **Audit trail:** Registrar cada ação executada com timestamp, executor e resultado
4. **Demo:** Executar `runbook_executor.py` e ver o motor de runbooks executando steps com tratamento de erro

---

## 💡 Conceitos-chave

- **Runbook-as-Code:** Representar procedimentos operacionais como código versionável no Git
- **Step executor:** Motor que executa cada step do runbook com retry, timeout e tratamento de erro
- **Audit log:** Registro imutável de todas as ações executadas (quem, quando, o quê, resultado)
- **Rollback strategy:** Conjunto de ações para desfazer uma remediação que piorou o incidente
- **Dry-run mode:** Executar o runbook simulando as ações sem efetivá-las (validação segura)

---

## 📂 Arquivos deste vídeo

```
video-4.2-runbooks/
├── README.md              ← Este arquivo
└── runbook_executor.py    ← Motor de Runbook-as-Code com auditoria e tratamento de erros
```

## ▶️ Como executar

```bash
python3 aula-04-automacao-e-resposta/video-4.2-runbooks/runbook_executor.py
```
