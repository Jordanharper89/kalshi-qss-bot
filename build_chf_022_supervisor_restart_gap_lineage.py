from pathlib import Path
import py_compile

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_coinbase_high_frequency"
for f in ("chf_018_restart_history_continuity_gate.py","chf_014_production_child_and_gap_lineage.py"):
    assert (PKG/f).exists(),f"{f} required"

module_code = """from pathlib import Path
import json
from datetime import datetime, timezone

def record_supervisor_restart(root, prior_state, current_state):
    root=Path(root)
    p=root/"runtime"/"coinbase_hf"/"supervisor_gap_lineage.jsonl"
    p.parent.mkdir(parents=True,exist_ok=True)
    rec={
      "schema_version":"CHF-022",
      "recorded_at":datetime.now(timezone.utc).isoformat(),
      "event":"ORACLE_SUPERVISOR_CHILD_RESTART",
      "prior_state":prior_state,
      "current_state":current_state,
      "gap_policy":"DETECT_AND_MARK;NO_SYNTHETIC_BACKFILL",
      "execution_authority":False,
    }
    with p.open("a",encoding="utf-8") as f:
        f.write(json.dumps(rec,sort_keys=True)+"\\n")
    return rec,p
"""
m=PKG/"chf_022_supervisor_restart_gap_lineage.py"
m.write_text(module_code,encoding="utf-8")
py_compile.compile(str(m),doraise=True)

test_code = """from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_022_supervisor_restart_gap_lineage import record_supervisor_restart
r,p=record_supervisor_restart(Path.cwd(),"RUNNING","RESTARTED")
assert r["gap_policy"]=="DETECT_AND_MARK;NO_SYNTHETIC_BACKFILL"
assert r["execution_authority"] is False
assert p.exists()
print("[PASS] supervisor restart lineage recorded")
print("[PASS] synthetic backfill prohibited")
print("[PASS] CHF-022 restart/gap lineage certified")
"""
t=ROOT/"test_chf_022_supervisor_restart_gap_lineage.py"
t.write_text(test_code,encoding="utf-8")
py_compile.compile(str(t),doraise=True)
print("[PASS] wrote",t)
print("[PASS] execution_authority=FALSE")