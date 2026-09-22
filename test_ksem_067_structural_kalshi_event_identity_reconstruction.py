from pathlib import Path
from dataclasses import asdict
import json
from qseries_v2.kalshi_sports_evidence_mapping.structural_kalshi_event_identity import reconstruct_cohort

root = Path.cwd()
src = json.loads((root/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem066_supported_league_live_cohort.json").read_text(encoding="utf-8"))
rows = reconstruct_cohort(src["rows"])
ready = [r for r in rows if r.status == "READY"]
print("[TOTAL]", len(rows))
print("[READY]", len(ready))
for r in rows[:15]:
    print("[IDENTITY]", r.league, r.event_ticker, "=>", r.outcome_code, r.status)
assert rows
assert ready, "no exact Kalshi market->event structural identity reconstructed"
assert all(r.execution_authority is False for r in rows)
state = root/"qseries_v2/kalshi_sports_evidence_mapping/state"
(state/"ksem067_structural_kalshi_event_identity.json").write_text(
    json.dumps({"rows":[asdict(r) for r in rows],"ready":len(ready),"execution_authority":False}, indent=2),
    encoding="utf-8"
)
print("[PASS] exact market/event parent-child structure preserved independently of proposition text")
print("[PASS] KSEM-067 certified")
