from pathlib import Path
import json
from qseries_v2.kalshi_sports_evidence_mapping.pre_freeze_gate import evaluate
root=Path.cwd(); r=evaluate(root); print("[GATE]",r)
assert r["mapping_ready"] and r["full_accounting"] and r["exact_bound_count"]>0
assert r["worker_heartbeat"] and r["launcher_surface_audited"]
assert r["execution_authority"] is False and r["probability_enabled"] is False
(root/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem075_pre_freeze_gate.json").write_text(json.dumps(r,indent=2),encoding="utf-8")
print("[PASS] KSEM worker/recovery/mapping boundary ready for exact launcher cutover")
print("[PASS] KSEM-075 certified as PRE-FREEZE gate; subsystem is NOT frozen until native launcher cutover is physically certified")
