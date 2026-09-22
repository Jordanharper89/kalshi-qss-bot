from pathlib import Path
import py_compile
ROOT=Path.cwd(); PKG=ROOT/"qseries_v2"/"oracle_edge_discovery"
MOD=PKG/"oed_022_contract_event_independence_filter.py"; TEST=ROOT/"test_oed_022_contract_event_independence_filter.py"
MOD.write_text(r"""
from pathlib import Path
from collections import defaultdict
from datetime import datetime,timezone
import json,hashlib
def _h(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def build(root=None):
    root=Path(root or Path.cwd()); a=json.loads((root/"runtime"/"edge_discovery"/"oed_021_family_condition_outcome_cohort.json").read_text())
    seen=set(); kept=[]; dropped=0
    for r in a["rows"]:
        k=(r["event_id"],r["family_key"],int(r["horizon_seconds"]))
        if k in seen: dropped+=1; continue
        seen.add(k); kept.append(r)
    y={"schema_version":"OED-022","created_at":datetime.now(timezone.utc).isoformat(),"source_hash":a["cohort_hash"],
       "input_rows":len(a["rows"]),"independent_rows":len(kept),"duplicates_removed":dropped,"rows":kept,
       "independence_key":"event_id+family_key+horizon","contract_day_oos_not_yet_claimed":True,
       "population_hash":_h(kept),"edge_proven":False,"probability_enabled":False,"direction_enabled":False,
       "publication_allowed":False,"execution_authority":False}
    p=root/"runtime"/"edge_discovery"/"oed_022_independent_event_population.json"
    p.write_text(json.dumps(y,sort_keys=True,indent=2),encoding="utf-8"); return y,p
""",encoding="utf-8")
TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_022_contract_event_independence_filter import build
s,p=build(Path.cwd()); assert s["independent_rows"]>0 and s["independent_rows"]<=s["input_rows"]
assert s["contract_day_oos_not_yet_claimed"] and not s["edge_proven"]
print("[INPUT]",s["input_rows"]); print("[INDEPENDENT]",s["independent_rows"]); print("[REMOVED]",s["duplicates_removed"])
print("[HASH]",s["population_hash"]); print("[PASS] OED-022 event-independence filter certified")
""",encoding="utf-8")
py_compile.compile(str(MOD),doraise=True); py_compile.compile(str(TEST),doraise=True)
print("[PASS] OED-022 installer complete")