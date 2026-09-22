from __future__ import annotations
import json
from pathlib import Path
SRC="runtime_state/solana_opportunities/solana_scanner/phase8_cross_family_nearest_neighbor_index.json"

def run(root):
 d=json.loads((Path(root)/SRC).read_text(encoding="utf-8"));rows=[]
 for x in d.get("indexed_cases",[]):
  vals=[n.get("forward_observational_return") for n in x.get("neighbors",[])
        if isinstance(n.get("forward_observational_return"),(int,float))]
  fams=sorted({n.get("family") for n in x.get("neighbors",[]) if n.get("family")})
  rows.append({"case_id":x["case_id"],"family":x["family"],
   "horizon_seconds":x["horizon_seconds"],"comparable_outcome_sample_size":len(vals),
   "comparable_family_count":len(fams),"comparable_families":fams,
   "raw_up_frequency":None if not vals else sum(v>0 for v in vals)/len(vals),
   "raw_down_frequency":None if not vals else sum(v<0 for v in vals)/len(vals),
   "mean_forward_observational_return":None if not vals else sum(vals)/len(vals),
   "calibrated_probability":None,"execution_authority":False})
 learnable=[x for x in rows if x["comparable_outcome_sample_size"]>=2]
 return {"revision":"USLS_161","case_count":len(rows),"learnable_case_count":len(learnable),
  "learned_cases":learnable,"all_cases":rows,
  "learning_semantics":"RAW_CROSS_FAMILY_EMPIRICAL_OUTCOMES_NOT_CALIBRATED_PROBABILITY",
  "next_boundary":"PHASE8_CROSS_FAMILY_LEARNING_CHECKPOINT",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_first_cross_family_empirical_learner.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
