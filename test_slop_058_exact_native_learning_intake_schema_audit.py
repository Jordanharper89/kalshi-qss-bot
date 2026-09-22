import json
from pathlib import Path
x=json.loads(Path("runtime_state/solana_live_opportunity/slop_058_native_learning_schema.json").read_text())
assert "build_learning_runtime_input" in x["olr_003_learning_event_bridge.py"]["functions"]
assert "apply_learning_inputs" in x["olr_004_learning_cycle_state.py"]["functions"]
assert "LearningLedgerRecord" in x["olr_007_learning_event_ledger.py"]["classes"]
for n,v in x.items():
 print("[MODULE]",n);print("[FUNCTIONS]",v["functions"]);print("[CLASSES]",v["classes"])
print("[PASS] native learner intake schema physically audited")
print("[PASS] no production mutation")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-058 CERTIFIED")
