#!/usr/bin/env python3
"""
loadgen.py — gerador de tráfego para o lab (rodar no host).

Dispara POST /checkout contra as DUAS versões (stable na 8001 e canary na 8002)
para que o Prometheus tenha dados reais e o canary_controller.py consiga
comparar stable vs canary. Sem esse tráfego não há métricas para analisar.

Só usa a biblioteca padrão do Python 3.10+ (urllib) — nenhum `pip install`.

Uso:
    python3 loadgen.py                 # tráfego contínuo até Ctrl+C
    python3 loadgen.py --rps 20        # ~20 requisições/s por versão
    python3 loadgen.py --duration 120  # roda por 120s e para
"""

import argparse
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime


def post(url: str) -> int:
    req = urllib.request.Request(url, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:
        return 0  # conexão recusada / timeout


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Gerador de tráfego para o checkout-service.")
    p.add_argument("--stable-url", default="http://localhost:8001/checkout")
    p.add_argument("--canary-url", default="http://localhost:8002/checkout")
    p.add_argument("--rps", type=float, default=10.0, help="requisições/s por versão (default: 10)")
    p.add_argument("--duration", type=float, default=0.0, help="segundos (0 = infinito)")
    args = p.parse_args(argv)

    delay = 1.0 / args.rps if args.rps > 0 else 0.0
    targets = {"stable": args.stable_url, "canary": args.canary_url}
    counters = {name: {"ok": 0, "err": 0} for name in targets}

    print(f"[loadgen] stable={args.stable_url}  canary={args.canary_url}")
    print(f"[loadgen] ~{args.rps:.0f} req/s por versão. Ctrl+C para parar.\n")

    start = time.time()
    last_report = start
    try:
        while True:
            for name, url in targets.items():
                status = post(url)
                bucket = "ok" if 200 <= status < 400 else "err"
                counters[name][bucket] += 1
            if delay:
                time.sleep(delay)

            now = time.time()
            if now - last_report >= 5.0:
                stamp = datetime.now().strftime("%H:%M:%S")
                parts = []
                for name in targets:
                    c = counters[name]
                    total = c["ok"] + c["err"]
                    rate = (c["ok"] / total * 100) if total else 0.0
                    parts.append(f"{name}: {total} reqs, {rate:.1f}% ok")
                print(f"[{stamp}] " + " | ".join(parts))
                last_report = now

            if args.duration and (now - start) >= args.duration:
                break
    except KeyboardInterrupt:
        print("\n[loadgen] interrompido.")

    print("\n[loadgen] resumo final:")
    for name in targets:
        c = counters[name]
        total = c["ok"] + c["err"]
        rate = (c["ok"] / total * 100) if total else 0.0
        print(f"  {name:7s} -> {total} reqs | {c['ok']} ok | {c['err']} erro | {rate:.1f}% sucesso")
    return 0


if __name__ == "__main__":
    sys.exit(main())
