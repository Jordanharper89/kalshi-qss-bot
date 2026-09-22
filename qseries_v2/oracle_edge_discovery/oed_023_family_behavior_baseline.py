
from pathlib import Path
from collections import defaultdict,Counter
from datetime import datetime,timezone
import json,hashlib
def _h(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def build(root=None):
    root=Path(root or Path.cwd()); a=json.loads((root/"runtime"/"edge_discovery"/"oed_022_independent_event_population.json").read_text())
    g=defaultdict(list)
    for r in a["rows"]: g[(r["family_key"],int(r["horizon_seconds"]))].append(r)
    rows=[]
    for (fam,h),rs in sorted(g.items()):
        c=Counter(r["behavior"] for r in rs); n=len(rs); best=max(c.values())/n
        rows.append({"family_key":fam,"horizon_seconds":h,"sample_size":n,"behavior_counts":dict(sorted(c.items())),
                     "majority_behavior_rate":best,"baseline_type":"WITHIN_FAMILY_MAJORITY_BEHAVIOR","edge_proven":False})
    y={"schema_version":"OED-023","created_at":datetime.now(timezone.utc).isoformat(),"source_hash":a["population_hash"],
       "groups":rows,"group_count":len(rows),"baseline_hash":_h(rows),"baseline_is_descriptive":True,
       "candidate_beats_baseline":False,"edge_proven":False,"probability_enabled":False,"direction_enabled":False,
       "publication_allowed":False,"execution_authority":False}
    p=root/"runtime"/"edge_discovery"/"oed_023_family_behavior_baseline.json"
    p.write_text(json.dumps(y,sort_keys=True,indent=2),encoding="utf-8"); return y,p
