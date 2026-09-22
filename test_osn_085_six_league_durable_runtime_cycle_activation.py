
from pathlib import Path
import json
from qseries_v2.oracle_source_network.runtime.six_league_durable_runtime_cycle import run_cycle, ADMITTED

rows,state=run_cycle(root=Path.cwd(),timeout=15)
assert tuple(r.league for r in rows)==ADMITTED
assert all(r.readback_count>0 for r in rows)
assert all(r.checkpoint_written for r in rows)
assert all(r.execution_authority is False for r in rows)
data=json.loads(state.read_text(encoding="utf-8"))
assert data["durable_runtime_cycle_ready"] is True
assert data["always_on_launcher_integration_certified"] is False
assert data["terminal_dependency"]=="NONE"
print("[STATE]",state)
print("[PASS] source -> canonical event -> PostgreSQL -> exact readback -> checkpoint completed for all six leagues")
print("[PASS] durable sports runtime cycle activated")
print("[PASS] always-on launcher integration intentionally NOT claimed")
print("[PASS] execution_authority=FALSE")
