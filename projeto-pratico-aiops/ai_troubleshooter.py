import urllib.request
import urllib.parse
import json
import time
from datetime import datetime

PROMETHEUS_URL = "http://localhost:9091/api/v1/query"

print("=" * 60)
print("🤖 AIOps Troubleshooter: Iniciando diagnóstico automático...")
print("=" * 60)
print(f"[{datetime.now().strftime('%H:%M:%S')}] Conectando ao Prometheus local...")

def query_prometheus(query: str):
    params = urllib.parse.urlencode({'query': query})
    url = f"{PROMETHEUS_URL}?{params}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        if response.status != 200:
            return None
        data = json.loads(response.read().decode('utf-8'))
        if data['status'] == 'success' and data['data']['result']:
            return float(data['data']['result'][0]['value'][1])
        return 0.0

try:
    # Coletar Error Rate
    error_query = 'sum(rate(http_requests_total{status="500"}[1m])) / sum(rate(http_requests_total[1m])) * 100'
    error_rate = query_prometheus(error_query)
    
    # Coletar Latência Média
    latency_query = 'rate(http_request_duration_seconds_sum[1m]) / rate(http_request_duration_seconds_count[1m])'
    latency = query_prometheus(latency_query)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Coleta concluída.")
    
    print(f"\n📊 DADOS ATUAIS (Último 1 minuto):")
    print(f"  • Taxa de Erro: {error_rate:.2f}%")
    print(f"  • Latência Média: {latency:.4f}s")
    
    print("\n🔍 ANÁLISE DO SISTEMA:")
    
    anomalies = []
    
    if error_rate > 5.0:
        anomalies.append(f"🔴 CRITICAL: Taxa de erros 500 está muito alta ({error_rate:.2f}%). O limite é 5%.")
    elif error_rate > 1.0:
        anomalies.append(f"🟡 WARNING: Taxa de erros acima do normal ({error_rate:.2f}%).")
        
    if latency > 1.0:
        anomalies.append(f"🔴 CRITICAL: Latência degradada ({latency:.2f}s). O alvo é < 0.2s.")
        
    if anomalies:
        for a in anomalies:
            print(a)
            
        print("\n🤖 CONCLUSÃO DA IA (Rule-based):")
        print("  Os sinais indicam que a aplicação está sob 'Chaos Mode'.")
        print("  Um pico de erros e latência simultâneo geralmente indica exaustão")
        print("  de recursos ou falha em dependência externa downstream.")
        print("\n  AÇÃO RECOMENDADA:")
        print("  Execute `curl -X POST http://localhost:8000/simulate-incident`")
        print("  para desligar o caos e restaurar o serviço.")
    else:
        print("🟢 Sistema Saudável. Nenhuma anomalia detectada nos últimos 60 segundos.")
        print("  Para simular um incidente, rode: `curl -X POST http://localhost:8000/simulate-incident`")
        
except Exception as e:
    print(f"\n❌ ERRO: Não foi possível conectar ao Prometheus.")
    print(f"O docker-compose está rodando? Erro: {e}")
