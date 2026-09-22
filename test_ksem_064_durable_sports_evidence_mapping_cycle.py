from pathlib import Path
from qseries_v2.kalshi_sports_evidence_mapping.durable_sports_evidence_mapping_cycle import run_cycle

root=Path.cwd()
a=run_cycle(root=root,max_tickers=25,timeout_seconds=15)
b=run_cycle(root=root,max_tickers=25,timeout_seconds=15)
print("[CYCLE_A]",len(a["rows"]),a["counts"],a["state_hash"])
print("[CYCLE_B]",len(b["rows"]),b["counts"],b["state_hash"])
assert a["rows"] and b["rows"]
assert all(x["execution_authority"] is False for x in b["rows"])
assert (root/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem_live_mapping_state.json").is_file()
print("[PASS] durable sports evidence mapping cycle ran twice and atomically checkpointed")
print("[PASS] KSEM-064 certified")
