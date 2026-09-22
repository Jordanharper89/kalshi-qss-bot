from pathlib import Path
import py_compile
ROOT=Path.cwd(); PKG=ROOT/"qseries_v2"/"oracle_edge_discovery"; PKG.mkdir(parents=True,exist_ok=True)
MOD=PKG/"oed_021_family_condition_outcome_cohort.py"; TEST=ROOT/"test_oed_021_family_condition_outcome_cohort.py"
MOD.write_text(r"""
from pathlib import Path
from collections import defaultdict
from datetime import datetime,timezone
import json,hashlib,re
def _h(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def _fam(t):
    m=re.match(r"^([A-Z0-9]+?)-",str(t)); return m.group(1) if m else str(t)
def build(root=None):
    root=Path(root or Path.cwd()); p=root/"runtime"/"edge_discovery"/"oed_018_behavior_classifications.json"
    x=json.loads(p.read_text(encoding="utf-8")); rows=[]
    for r in x["classifications"]:
        ts=r.get("tickers") or ([r["ticker"]] if r.get("ticker") else [])
        fams=sorted(set(_fam(t) for t in ts))
        rows.append({**r,"families":fams,"family_key":"|".join(fams)})
    rows.sort(key=lambda r:(r["family_key"],int(r["horizon_seconds"]),r["event_id"]))
    y={"schema_version":"OED-021","created_at":datetime.now(timezone.utc).isoformat(),"rows":rows,
       "row_count":len(rows),"cohort_hash":_h(rows),"family_identity_physical":True,"edge_proven":False,
       "probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}
    q=root/"runtime"/"edge_discovery"/"oed_021_family_condition_outcome_cohort.json"
    q.write_text(json.dumps(y,sort_keys=True,indent=2),encoding="utf-8"); return y,q
""",encoding="utf-8")
TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_021_family_condition_outcome_cohort import build
s,p=build(Path.cwd()); assert s["row_count"]>0 and s["family_identity_physical"] and not s["edge_proven"]
print("[COHORT]",p); print("[ROWS]",s["row_count"]); print("[HASH]",s["cohort_hash"])
from collections import Counter
print("[TOP_FAMILIES]",Counter(x["family_key"] for x in s["rows"]).most_common(25))
print("[PASS] OED-021 family-conditioned outcome cohort certified")
""",encoding="utf-8")
py_compile.compile(str(MOD),doraise=True); py_compile.compile(str(TEST),doraise=True)
print("[PASS] OED-021 installer complete")