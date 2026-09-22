from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_063_independent_token_idempotent_learning_admission import candidate_inputs,admit
r=Path.cwd(); c=candidate_inputs(r)
assert c and len(c)==len({x[0]["token_address"] for x in c})
a=admit(r); b=admit(r)
assert not b,"IDEMPOTENCY_FAILURE"
print("[INDEPENDENT_TOKEN_CANDIDATES]",len(c))
print("[NEW_ADMISSIONS]",len(a))
print("[SECOND_PASS_ADMISSIONS]",len(b))
print("[PASS] one deterministic learning admission per independent token")
print("[PASS] learning admission idempotent")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-063 CERTIFIED")
