
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
