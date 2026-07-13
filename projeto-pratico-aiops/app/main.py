import asyncio
import random
import time
from fastapi import FastAPI, HTTPException, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="Checkout Service")

# Prometheus Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])

# State for chaos engineering
chaos_mode = False

@app.middleware("http")
async def monitor_requests(request, call_next):
    start_time = time.time()
    
    # Introduce chaos if enabled
    if chaos_mode and request.url.path == "/checkout":
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
    try:
        response = await call_next(request)
        status_code = response.status_code
        
        # More chaos! Fail 40% of checkouts
        if chaos_mode and request.url.path == "/checkout" and random.random() < 0.4:
            status_code = 500
            
    except Exception as e:
        status_code = 500
        raise e
    finally:
        latency = time.time() - start_time
        REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=status_code).inc()
        REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(latency)
        
    return response

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
def health():
    return {"status": "UP"}

@app.post("/checkout")
async def checkout():
    # Simulate DB/Payment processing
    await asyncio.sleep(random.uniform(0.05, 0.15))
    if chaos_mode and random.random() < 0.4:
        raise HTTPException(status_code=500, detail="Payment Gateway Timeout")
    return {"status": "SUCCESS", "transaction_id": f"txn-{random.randint(1000, 9999)}"}

@app.post("/simulate-incident")
def trigger_incident():
    global chaos_mode
    chaos_mode = not chaos_mode
    state = "ENABLED" if chaos_mode else "DISABLED"
    return {"message": f"Chaos mode {state}"}

# Background task to generate normal traffic
async def generate_traffic():
    while True:
        try:
            start = time.time()
            latency = random.uniform(0.05, 0.15)
            if chaos_mode:
                latency += random.uniform(0.5, 2.0)
                if random.random() < 0.4:
                    REQUEST_COUNT.labels(method="POST", endpoint="/checkout", status=500).inc()
                else:
                    REQUEST_COUNT.labels(method="POST", endpoint="/checkout", status=200).inc()
            else:
                REQUEST_COUNT.labels(method="POST", endpoint="/checkout", status=200).inc()
                
            REQUEST_LATENCY.labels(method="POST", endpoint="/checkout").observe(latency)
            
            # 10 req/s normal, slightly more erratic during chaos
            await asyncio.sleep(0.1 if not chaos_mode else random.uniform(0.05, 0.2))
        except Exception:
            pass

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(generate_traffic())
