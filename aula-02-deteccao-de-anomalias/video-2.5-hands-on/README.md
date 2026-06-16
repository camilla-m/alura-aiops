# Vídeo 2.5 — Hands-on: Configurando detecção de anomalias

## 🎬 Roteiro

**Tipo:** Prática Guiada  
**Habilidade:** Implementar um monitor inteligente de ponta a ponta combinando detecção de anomalias, baseline dinâmico e previsão de capacidade.

### Desenvolvimento

1. **Exercício 1:** Aplicar Z-Score em métricas de CPU e identificar anomalias reais vs. falsos positivos do threshold estático
2. **Exercício 2:** Configurar um baseline dinâmico com EMA para a mesma métrica
3. **Exercício 3:** Rodar o forecast de capacidade de disco e calcular o TTL
4. **Relatório final:** Consolidar os resultados em um relatório de monitoramento inteligente

---

## 💡 O que você vai praticar

- Comparar threshold estático vs. Z-Score nos mesmos dados
- Entender como a sazonalidade afeta a detecção de anomalias
- Calcular projeções de capacidade com regressão linear
- Interpretar os resultados e tomar decisões operacionais

---

## 📂 Arquivos deste vídeo

```
video-2.5-hands-on/
├── README.md            ← Este arquivo
└── smart_monitor_lab.py ← Laboratório completo de detecção e forecast
```

## ▶️ Como executar

```bash
python3 aula-02-deteccao-de-anomalias/video-2.5-hands-on/smart_monitor_lab.py
```

---

## 🎓 Ao final deste hands-on você terá:

- ✔ Detectado anomalias com dois métodos diferentes
- ✔ Comparado a eficácia de cada abordagem
- ✔ Calculado o TTL de um recurso em crescimento
- ✔ Gerado um relatório de monitoramento inteligente
