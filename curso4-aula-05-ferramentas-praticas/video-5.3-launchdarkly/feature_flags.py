"""
Vídeo 5.3 — LaunchDarkly: feature flags com targeting e rollout
================================================================
Implementa um mini feature-flag engine no estilo LaunchDarkly:
flags com targeting rules por atributo de usuário (plano, país,
%rollout), percentage rollout determinístico por hash da userKey
e um kill switch global por flag. Avalia várias flags para vários
usuários de exemplo e mostra a variation servida e o motivo.

Mapeamento com os conceitos reais do LaunchDarkly:
- Flag        → chave que controla comportamento em runtime, sem deploy.
- Variation   → os valores possíveis (aqui true/false, mas pode ser
                multivariado: control/treatment, ou objetos JSON).
- Context/User→ objeto com key + atributos avaliados pelas regras.
- Targeting rule → clauses (attribute op values) que servem uma variation.
- Rollout     → bucketing determinístico por hash(flagKey + userKey);
                o LaunchDarkly usa o mesmo princípio para consistência.
- Off variation / kill switch → quando o targeting está OFF, todos
                recebem a off variation instantaneamente.

Conceitos demonstrados:
- Avaliação de regras em ordem (primeira que casa vence)
- Bucketing determinístico e estável por usuário
- Fallthrough (rollout padrão) e off variation
- Reason da avaliação (auditável, como o LaunchDarkly retorna)
"""

import hashlib
from dataclasses import dataclass, field
from enum import Enum

BUCKET_SCALE = 100_000  # granularidade do bucketing (LaunchDarkly usa 100000)


class Op(str, Enum):
    IN = "in"
    NOT_IN = "notIn"


@dataclass
class Clause:
    """Uma condição de targeting: attribute <op> values."""
    attribute: str
    op: Op
    values: list

    def matches(self, ctx: dict) -> bool:
        actual = ctx.get(self.attribute)
        if self.op is Op.IN:
            return actual in self.values
        return actual not in self.values


@dataclass
class Rule:
    """Regra de targeting: se TODAS as clauses casam, serve a variation."""
    clauses: list[Clause]
    variation: bool
    description: str = ""

    def matches(self, ctx: dict) -> bool:
        return all(c.matches(ctx) for c in self.clauses)


@dataclass
class Flag:
    key: str
    on: bool                      # kill switch: False → serve off_variation
    rules: list[Rule] = field(default_factory=list)
    fallthrough_rollout: int = 0  # % que recebe True quando nenhuma regra casa
    off_variation: bool = False


@dataclass
class Evaluation:
    value: bool
    reason: str


def bucket(flag_key: str, user_key: str) -> float:
    """
    Bucketing determinístico 0..100 por hash(flagKey + userKey).
    O mesmo usuário sempre cai no mesmo ponto para o mesmo flag,
    garantindo experiência consistente entre requisições.
    """
    digest = hashlib.sha1(f"{flag_key}:{user_key}".encode()).hexdigest()
    # usa os primeiros 15 hex chars como inteiro, normaliza para 0..100
    n = int(digest[:15], 16)
    return (n % BUCKET_SCALE) / BUCKET_SCALE * 100.0


def evaluate(flag: Flag, ctx: dict) -> Evaluation:
    """Retorna a variation servida e o motivo (estilo LDReason)."""
    if not flag.on:
        return Evaluation(flag.off_variation, "OFF (kill switch)")

    for i, rule in enumerate(flag.rules):
        if rule.matches(ctx):
            return Evaluation(rule.variation, f"RULE_MATCH[{i}] {rule.description}")

    # Fallthrough: percentage rollout determinístico
    b = bucket(flag.key, ctx["key"])
    if b < flag.fallthrough_rollout:
        return Evaluation(True, f"FALLTHROUGH rollout (bucket {b:.1f} < {flag.fallthrough_rollout}%)")
    return Evaluation(False, f"FALLTHROUGH default (bucket {b:.1f} ≥ {flag.fallthrough_rollout}%)")


# ---------------------------------------------------------------------------
# Configuração de flags de exemplo
# ---------------------------------------------------------------------------

FLAGS = {
    "new-checkout-ui": Flag(
        key="new-checkout-ui",
        on=True,
        rules=[
            Rule([Clause("plan", Op.IN, ["enterprise"]),
                  Clause("country", Op.IN, ["BR", "PT"])],
                 variation=True, description="enterprise + BR/PT → ON"),
            Rule([Clause("email", Op.IN, ["ceo@acme.com"])],
                 variation=True, description="individual target (CEO)"),
        ],
        fallthrough_rollout=20,  # 20% dos demais usuários
        off_variation=False,
    ),
    "beta-ai-assistant": Flag(
        key="beta-ai-assistant",
        on=True,
        rules=[
            Rule([Clause("plan", Op.NOT_IN, ["free"])],
                 variation=True, description="qualquer plano pago → ON"),
        ],
        fallthrough_rollout=0,
        off_variation=False,
    ),
    "risky-payment-provider": Flag(
        key="risky-payment-provider",
        on=False,  # kill switch acionado após incidente
        rules=[
            Rule([Clause("country", Op.IN, ["BR"])], variation=True,
                 description="Brasil → ON"),
        ],
        fallthrough_rollout=50,
        off_variation=False,
    ),
}

USERS = [
    {"key": "u-1001", "email": "ana@acme.com",   "plan": "enterprise", "country": "BR"},
    {"key": "u-1002", "email": "beto@startup.io","plan": "pro",        "country": "US"},
    {"key": "u-1003", "email": "ceo@acme.com",   "plan": "enterprise", "country": "US"},
    {"key": "u-1004", "email": "dora@free.com",  "plan": "free",       "country": "BR"},
    {"key": "u-1005", "email": "edu@loja.pt",    "plan": "pro",        "country": "PT"},
    {"key": "u-1006", "email": "fer@web.br",     "plan": "free",       "country": "BR"},
]


def run_demo() -> None:
    print("=" * 70)
    print("🚩 LaunchDarkly-style Feature Flag Engine")
    print("   Curso 4 — CI/CD Inteligente")
    print("=" * 70)

    for flag_key, flag in FLAGS.items():
        state = "ON" if flag.on else "OFF (kill switch)"
        print("\n" + "─" * 70)
        print(f"🏳️  Flag '{flag_key}'  [targeting: {state}, "
              f"fallthrough rollout: {flag.fallthrough_rollout}%]")
        print("─" * 70)
        print(f"  {'Usuário':<9} {'plano':<11} {'país':<5} {'variation':<10} motivo")
        print(f"  {'─'*9} {'─'*11} {'─'*5} {'─'*10} {'─'*30}")
        served_true = 0
        for u in USERS:
            ev = evaluate(flag, u)
            served_true += int(ev.value)
            served = "✅ true" if ev.value else "⬜ false"
            print(f"  {u['key']:<9} {u['plan']:<11} {u['country']:<5} {served:<10} {ev.reason}")
        print(f"\n  → {served_true}/{len(USERS)} usuários receberam a feature.")

    # Demonstra determinismo do bucketing
    print("\n" + "=" * 70)
    print("🔁 Determinismo do rollout (mesmo usuário → mesmo bucket sempre)")
    print("=" * 70)
    u = USERS[1]
    buckets = {bucket("new-checkout-ui", u["key"]) for _ in range(1000)}
    print(f"  1000 avaliações de '{u['key']}' no flag 'new-checkout-ui' → "
          f"buckets distintos: {len(buckets)} (esperado: 1)")
    print(f"  Bucket estável: {buckets.pop():.2f}")

    print("\n" + "=" * 70)
    print("📌 CONCLUSÃO")
    print("=" * 70)
    print("""
  Feature flags separam DEPLOY de RELEASE: o código já está em produção,
  mas o comportamento é ligado por targeting rules e rollout gradual,
  sem redeploy. O bucketing por hash garante que cada usuário vê a mesma
  variation de forma consistente, e o kill switch desliga tudo em 1 clique
  quando algo dá errado — exatamente o modelo do LaunchDarkly.

  No Vídeo 5.4, olhamos para a saúde dos TESTES com Buildkite Test
  Analytics: reliability, flaky tests e slow tests.
    """)


if __name__ == "__main__":
    run_demo()
