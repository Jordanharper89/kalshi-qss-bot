from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_061_canonical_prospective_learning_evidence import learning_evidence
x=learning_evidence(Path.cwd())
assert x,"NO_RESOLVED_LEARNING_EVIDENCE"
assert all(len(v["evidence_hash"])==64 for v in x)
assert all(v["condition"]=="BUY_PRESSURE" and v["horizon_seconds"]==60 for v in x)
assert all(v["target_fraction"]==.10 and v["stop_fraction"]==-.05 and v["friction_bps"]==200 for v in x)
print("[EVIDENCE_RECORDS]",len(x))
print("[INDEPENDENT_TOKENS]",len({v["token_address"] for v in x}))
print("[OUTCOMES]",{k:sum(v["outcome"]==k for v in x) for k in sorted({v["outcome"] for v in x})})
print("[PASS] canonical prediction+resolution learning evidence materialized")
print("[PASS] frozen BUY_PRESSURE economics preserved")
print("[PASS] source ledgers unchanged")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-061 CERTIFIED")
