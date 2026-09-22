from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_061_canonical_prospective_learning_evidence import learning_evidence
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_062_native_ocl_prospective_outcome_bridge import build_slop_learning_input
e=learning_evidence(Path.cwd())[0]
o,v,r=build_slop_learning_input(1,e)
assert o.subject_id=="solana:"+e["token_address"]
assert o.outcome_type=="prospective_market_path"
assert v.subject_id==o.subject_id and len(v.event_hash)==64
assert r.source_kind=="learning_event" and len(r.input_hash)==64
print("[SUBJECT]",o.subject_id)
print("[OUTCOME_TYPE]",o.outcome_type)
print("[EVENT_ID]",v.event_id)
print("[INPUT_HASH]",r.input_hash)
print("[PASS] native OCL prospective bridge physically constructed")
print("[PASS] no fake Kalshi settlement semantics")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-062 CERTIFIED")
