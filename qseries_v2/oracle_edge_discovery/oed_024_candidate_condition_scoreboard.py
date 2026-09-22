
from pathlib import Path
from collections import defaultdict,Counter
from datetime import datetime,timezone
import json,hashlib
def _h(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def build(root=None):
    root=Path(root or Path.cwd())
    a=json.loads((root/"runtime"/"edge_discovery"/"oed_022_independent_event_population.json").read_text())
    b=json.loads((root/"runtime"/"edge_discovery"/"oed_023_family_behavior_baseline.json").read_text())
    base={(x["family_key"],int(x["horizon_seconds"])):x for x in b["groups"]}; g=defaultdict(list)
    for r in a["rows"]:
        if r["detector_family"]=="CROSS_CONTRACT_DISPERSION":
            z=abs(float(r.get("initial_gap",0))); mag="LT_20C" if z<.2 else ("20_TO_40C" if z<.4 else "GE_40C")
        else:
            z=abs(float(r.get("signal_return",0))); mag="LT_5BP" if z<.0005 else ("5_TO_10BP" if z<.001 else "GE_10BP")
        g[(r["detector_family"],r["family_key"],int(r["horizon_seconds"]),mag)].append(r)
    rows=[]
    for k,rs in sorted(g.items()):
        c=Counter(r["behavior"] for r in rs); n=len(rs); winner,count=c.most_common(1)[0]; br=base[(k[1],k[2])]["majority_behavior_rate"]; rate=count/n
        rows.append({"detector_family":k[0],"family_key":k[1],"horizon_seconds":k[2],"magnitude_bucket":k[3],
                     "sample_size":n,"dominant_behavior":winner,"dominant_rate":rate,"family_baseline_rate":br,
                     "raw_lift_over_baseline":rate-br,"status":"RESEARCH_ONLY","oos_validated":False,"edge_proven":False})
    rows.sort(key=lambda x:(-x["raw_lift_over_baseline"],-x["sample_size"],x["family_key"]))
    y={"schema_version":"OED-024","created_at":datetime.now(timezone.utc).isoformat(),"scoreboard":rows,
       "candidate_groups":len(rows),"scoreboard_hash":_h(rows),"ranking_is_discovery_only":True,
       "multiple_testing_uncontrolled":True,"oos_validated":False,"certified_edge_count":0,"edge_proven":False,
       "probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}
    p=root/"runtime"/"edge_discovery"/"oed_024_candidate_condition_scoreboard.json"
    p.write_text(json.dumps(y,sort_keys=True,indent=2),encoding="utf-8"); return y,p
