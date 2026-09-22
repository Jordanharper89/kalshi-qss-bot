from __future__ import annotations
import json,math
from pathlib import Path

SRC="runtime_state/solana_opportunities/solana_scanner/phase8_leakage_safe_feature_snapshots.json"

def bucket(v,step):
 if v is None:return None
 try:return round(float(v)/step)*step
 except Exception:return None

def run(root):
 d=json.loads((Path(root)/SRC).read_text(encoding="utf-8"));groups={}
 for x in d.get("snapshots",[]):
  f=x.get("features") or {}
  key=(x.get("prediction_horizon_seconds"),
       bucket(f.get("return_to_cutoff"),0.05),
       bucket(f.get("mfe_to_cutoff"),0.05),
       bucket(f.get("mae_to_cutoff"),0.05),
       min(int(f.get("trade_count_to_cutoff") or 0),20))
  groups.setdefault(key,[]).append(x)
 rows=[]
 for key,xs in groups.items():
  outs=[float(x["forward_observational_return"]) for x in xs
        if isinstance(x.get("forward_observational_return"),(int,float))]
  families=sorted({x.get("family") for x in xs if x.get("family")})
  rows.append({"horizon_seconds":key[0],"return_bucket":key[1],"mfe_bucket":key[2],
   "mae_bucket":key[3],"trade_count_bucket":key[4],
   "sample_size":len(xs),"outcome_sample_size":len(outs),
   "family_count":len(families),"families":families,
   "raw_up_frequency":None if not outs else sum(v>0 for v in outs)/len(outs),
   "raw_down_frequency":None if not outs else sum(v<0 for v in outs)/len(outs),
   "mean_forward_observational_return":None if not outs else sum(outs)/len(outs),
   "calibrated_probability":None})
 return {"revision":"USLS_156","comparable_group_count":len(rows),"groups":rows,
  "probability_semantics":"RAW_EMPIRICAL_FREQUENCY_ONLY_NOT_CALIBRATED_PROBABILITY",
  "next_boundary":"FIRST_CROSS_LAUNCH_FEATURE_LEARNING_DIAGNOSTIC",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_cross_launch_comparable_case_index.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
