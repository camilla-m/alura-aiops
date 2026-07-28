#!/usr/bin/env python3
"""
canary_controller.py — o "Argo Rollouts local" do Curso 4.

Este script reproduz, sem Kubernetes, a lógica de um `Rollout` com estratégia
canary + `AnalysisTemplate` do Argo Rollouts:

    setWeight 10 -> analysis -> setWeight 25 -> analysis ->
    setWeight 50 -> analysis -> setWeight 100 (PROMOTE)

Em cada "gate" ele consulta o Prometheus (as MÉTRICAS REAIS do canary v2 que o
docker-compose está expondo) e compara com o baseline do stable v1:

    - Success rate do canary  >= limite (default 95%)
    - Latência p95 do canary  <= teto absoluto (default 0.5s)
    - Latência p95 do canary  <= p95 do stable * fator (comparação estatística)

Se qualquer gate reprovar em número suficiente de amostras, ele ABORTA e faz
ROLLBACK (volta o peso para 0). Se todos passarem, ele PROMOVE o canary.

Depende apenas da biblioteca padrão do Python 3.10+ (urllib) — roda no host,
sem `pip install`.

Uso típico (com o docker-compose deste lab no ar):

    python3 canary_controller.py
    python3 canary_controller.py --prometheus-url http://localhost:9090
    python3 canary_controller.py --min-success 0.98 --max-p95 0.3
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

# Passos de peso do rollout (o mesmo que `setWeight` no Argo Rollouts).
DEFAULT_STEPS = [10, 25, 50, 100]


def ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def log(msg: str) -> None:
    print(f"[{ts()}] {msg}", flush=True)


# --------------------------------------------------------------------------- #
# Cliente Prometheus (stdlib)
# --------------------------------------------------------------------------- #
class Prometheus:
    def __init__(self, base_url: str):
        self.query_url = base_url.rstrip("/") + "/api/v1/query"

    def query(self, promql: str):
        params = urllib.parse.urlencode({"query": promql})
        url = f"{self.query_url}?{params}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("status") != "success":
            return None
        result = data["data"]["result"]
        if not result:
            return None
        return float(result[0]["value"][1])

    def scalar(self, promql: str, default=None):
        """Retorna o valor escalar da query ou `default` se não houver série
        (ex.: canary ainda sem tráfego)."""
        try:
            value = self.query(promql)
            return default if value is None else value
        except (urllib.error.URLError, ValueError, KeyError) as exc:
            raise RuntimeError(f"falha ao consultar o Prometheus: {exc}") from exc


# --------------------------------------------------------------------------- #
# Métricas RED por versão
# --------------------------------------------------------------------------- #
def success_rate(prom: Prometheus, version: str):
    q = (
        f'sum(rate(http_requests_total{{version="{version}",status=~"2.."}}[1m]))'
        f' / sum(rate(http_requests_total{{version="{version}"}}[1m]))'
    )
    # Sem tráfego -> None (tratado como "sem dados ainda").
    return prom.scalar(q, default=None)


def p95_latency(prom: Prometheus, version: str):
    q = (
        "histogram_quantile(0.95, sum(rate("
        f'http_request_duration_seconds_bucket{{version="{version}"}}[1m]'
        ")) by (le))"
    )
    return prom.scalar(q, default=None)


# --------------------------------------------------------------------------- #
# Análise (equivalente ao AnalysisTemplate do Argo Rollouts)
# --------------------------------------------------------------------------- #
def analyse(prom, args, weight):
    """Roda N medições do canary contra o baseline do stable. Reprova se o
    número de medições ruins atingir `failure_limit` (mesma semântica de
    `failureLimit` do Argo Rollouts). Retorna (aprovado: bool, motivo: str)."""
    failures = 0
    for i in range(1, args.measurements + 1):
        canary_sr = success_rate(prom, args.canary_version)
        canary_p95 = p95_latency(prom, args.canary_version)
        stable_p95 = p95_latency(prom, args.stable_version)

        if canary_sr is None or canary_p95 is None:
            log(f"   medição {i}/{args.measurements}: ⏳ sem dados do canary ainda (aguardando tráfego)")
            time.sleep(args.interval)
            continue

        rel_limit = (stable_p95 * args.p95_factor) if stable_p95 else float("inf")
        problems = []
        if canary_sr < args.min_success:
            problems.append(
                f"success {canary_sr * 100:.1f}% < {args.min_success * 100:.0f}%"
            )
        if canary_p95 > args.max_p95:
            problems.append(f"p95 {canary_p95:.3f}s > teto {args.max_p95:.3f}s")
        if canary_p95 > rel_limit:
            problems.append(
                f"p95 {canary_p95:.3f}s > {args.p95_factor:.1f}x stable ({rel_limit:.3f}s)"
            )

        stable_txt = f"{stable_p95:.3f}s" if stable_p95 is not None else "n/a"
        if problems:
            failures += 1
            log(
                f"   medição {i}/{args.measurements}: 🔴 canary sr={canary_sr * 100:.1f}% "
                f"p95={canary_p95:.3f}s (stable p95={stable_txt}) -> {'; '.join(problems)}"
            )
        else:
            log(
                f"   medição {i}/{args.measurements}: 🟢 canary sr={canary_sr * 100:.1f}% "
                f"p95={canary_p95:.3f}s (stable p95={stable_txt}) OK"
            )

        if failures >= args.failure_limit:
            return False, f"{failures} medição(ões) ruim(s) no peso {weight}% (limite {args.failure_limit})"

        time.sleep(args.interval)

    return True, f"análise aprovada no peso {weight}%"


# --------------------------------------------------------------------------- #
# Orquestração do rollout
# --------------------------------------------------------------------------- #
def run_rollout(prom, args) -> int:
    print("=" * 68)
    print("🚦 CANARY CONTROLLER — Argo Rollouts (modo local, PATH A)")
    print("=" * 68)
    log(f"stable = {args.stable_version} | canary = {args.canary_version}")
    log(
        f"gates: success >= {args.min_success * 100:.0f}% | "
        f"p95 <= {args.max_p95:.3f}s | p95 <= {args.p95_factor:.1f}x stable"
    )
    log(f"passos (setWeight): {args.steps}")
    print("-" * 68)

    for weight in args.steps:
        log(f"➡️  setWeight {weight}%  — encaminhando {weight}% do tráfego para o canary")

        if weight >= 100:
            log("🎉 último passo alcançado sem reprovações.")
            break

        log(f"⏸️  pause + analysis (janela de {args.measurements * args.interval:.0f}s)...")
        approved, reason = analyse(prom, args, weight)

        if not approved:
            print("-" * 68)
            log(f"❌ ANÁLISE REPROVADA: {reason}")
            log("↩️  ROLLBACK automático: setWeight 0% — 100% do tráfego volta para o stable.")
            log(f"    (equivale a `kubectl argo rollouts abort {args.rollout_name}`)")
            print("=" * 68)
            print("RESULTADO: 🔴 ROLLBACK — o canary v2 foi descartado, produção segue no v1.")
            print("=" * 68)
            return 1

        log(f"✅ {reason} — promovendo para o próximo passo.")
        print("-" * 68)

    print("=" * 68)
    log("🟢 PROMOTE: todos os gates passaram. setWeight 100% — canary vira o novo stable.")
    log(f"    (equivale a `kubectl argo rollouts promote {args.rollout_name}`)")
    print("RESULTADO: 🟢 PROMOÇÃO — o canary v2 é agora a versão estável.")
    print("=" * 68)
    return 0


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Argo Rollouts canary analysis, versão local.")
    p.add_argument("--prometheus-url", default="http://localhost:9090")
    p.add_argument("--stable-version", default="v1")
    p.add_argument("--canary-version", default="v2")
    p.add_argument("--rollout-name", default="checkout")
    p.add_argument("--steps", default="10,25,50,100",
                   help="pesos do canary separados por vírgula (default: 10,25,50,100)")
    p.add_argument("--min-success", type=float, default=0.95,
                   help="success rate mínimo do canary (default: 0.95)")
    p.add_argument("--max-p95", type=float, default=0.5,
                   help="teto absoluto de p95 do canary em segundos (default: 0.5)")
    p.add_argument("--p95-factor", type=float, default=1.5,
                   help="canary p95 <= fator * stable p95 (default: 1.5)")
    p.add_argument("--measurements", type=int, default=4,
                   help="número de medições por gate (default: 4)")
    p.add_argument("--interval", type=float, default=10.0,
                   help="segundos entre medições (default: 10)")
    p.add_argument("--failure-limit", type=int, default=2,
                   help="medições ruins que reprovam o gate (default: 2)")
    args = p.parse_args(argv)
    args.steps = [int(x) for x in args.steps.split(",") if x.strip()]
    return args


def main(argv=None) -> int:
    args = parse_args(argv)
    prom = Prometheus(args.prometheus_url)
    try:
        prom.scalar("vector(1)", default=None)  # smoke test de conexão
    except RuntimeError as exc:
        log(f"❌ {exc}")
        log("O docker-compose está no ar? Tente: docker compose up --build")
        return 2
    return run_rollout(prom, args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[interrompido pelo usuário]")
        sys.exit(130)
