from __future__ import annotations
import hashlib,json,time
from pathlib import Path
HORIZONS=(5,15,30,60,300,900)

def freeze(opportunity:dict,formula_result:dict,created_at=None)->list[dict]:
 now=created_at or time.time();out=[]
 asset=str(opportunity["asset_key"]);formula=formula_result["formula"]
 for h in HORIZONS:
  raw=f"{asset}|{formula}|{now}|{h}"
  out.append({"thesis_id":hashlib.sha256(raw.encode()).hexdigest(),"asset_key":asset,
   "formula":formula,"horizon_seconds":h,"frozen_at":now,
   "historical_sample_size":formula_result.get("sample_size"),
   "historical_mean_return":formula_result.get("mean_return"),
   "historical_positive_frequency":formula_result.get("positive_frequency"),
   "calibrated_probability":None,"prospective":True,
   "execution_authority":False,"read_only":True})
 return out

def write(root:Path,rows:list[dict])->Path:
 p=root/"runtime_state/solana_opportunities/theses/prospective_formula_theses.jsonl";p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("a",encoding="utf-8") as f:
  for r in rows:f.write(json.dumps(r,sort_keys=True)+"\n")
 return p
