from __future__ import annotations
import json,math,statistics
from pathlib import Path

SRC="runtime_state/solana_opportunities/solana_scanner/phase8_enriched_feature_snapshots.json"
FEATURES=("trade_velocity","quote_volume_velocity","return_to_cutoff","mfe_to_cutoff","mae_to_cutoff")

def _num(v):
 try:
  x=float(v);return x if math.isfinite(x) else None
 except Exception:return None

def run(root):
 d=json.loads((Path(root)/SRC).read_text(encoding="utf-8"));rows=d.get("snapshots",[])
 scales={}
 for k in FEATURES:
  vals=[_num(x.get("features",{}).get(k)) for x in rows]
  vals=[v for v in vals if v is not None]
  med=statistics.median(vals) if vals else 0.0
  mad=statistics.median([abs(v-med) for v in vals]) if len(vals)>1 else 1.0
  scales[k]={"median":med,"scale":mad if mad>1e-12 else 1.0}
 indexed=[]
 for a in rows:
  cand=[]
  for b in rows:
   if a is b or a.get("family")==b.get("family"):continue
   if a.get("horizon_seconds")!=b.get("horizon_seconds"):continue
   terms=[]
   for k in FEATURES:
    av=_num(a.get("features",{}).get(k));bv=_num(b.get("features",{}).get(k))
    if av is None or bv is None:continue
    terms.append(((av-bv)/scales[k]["scale"])**2)
   if len(terms)<3:continue
   dist=(sum(terms)/len(terms))**0.5
   cand.append((dist,b))
  cand.sort(key=lambda z:z[0])
  nn=[{"case_id":b["case_id"],"family":b["family"],"distance":dist,
       "forward_observational_return":b.get("forward_observational_return")}
      for dist,b in cand[:10]]
  indexed.append({"case_id":a["case_id"],"family":a["family"],
    "horizon_seconds":a["horizon_seconds"],"neighbor_count":len(nn),"neighbors":nn})
 return {"revision":"USLS_160","indexed_case_count":len(indexed),
  "cases_with_cross_family_neighbors":sum(x["neighbor_count"]>0 for x in indexed),
  "feature_scales":scales,"indexed_cases":indexed,
  "similarity_semantics":"ROBUST_SCALED_DISTANCE_ON_COMMON_PRE_CUTOFF_FEATURES",
  "next_boundary":"FIRST_CROSS_FAMILY_EMPIRICAL_LEARNER",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_cross_family_nearest_neighbor_index.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
