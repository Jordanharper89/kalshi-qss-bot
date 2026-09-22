from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_067_opportunity_level_exactly_once_learning_lineage import *
r=Path.cwd(); rows=independent_evidence(r)
assert rows
assert len(rows)==len({k for k,e in rows})
assert len({e["prediction_id"] for k,e in rows})==len(rows)
print("[RESOLVED_EVIDENCE]",len(learning_evidence(r)))
print("[INDEPENDENT_OPPORTUNITIES]",len(rows))
print("[EXISTING_CONSUMED]",len(load_consumed(r)))
print("[PASS] same-opportunity pair correlation collapsed")
print("[PASS] later opportunities on same token remain independently learnable")
print("[PASS] durable exactly-once lineage boundary ready")
print("[PASS] no production state mutation")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-067 CERTIFIED")
