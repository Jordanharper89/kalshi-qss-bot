from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path

FEATURES=("liquidity","buy_sell_imbalance","swap_velocity","wallet_concentration","smart_money_flow",
          "holder_concentration","freeze_authority","mint_authority","pool_depth","volume_acceleration",
          "price_acceleration","sol_regime")

def _ts(v):
 if isinstance(v,(int,float)):return float(v)
 s=str(v).replace("Z","+00:00")
 return datetime.fromisoformat(s).timestamp()

def build(current:dict,history:list[dict])->dict:
 cutoff=_ts(current["observed_at"]);cases=[]
 for row in history:
  observed=row.get("observed_at")
  if observed is None:continue
  try:t=_ts(observed)
  except Exception:continue
  if t>=cutoff:continue
  feats={k:row.get(k) for k in FEATURES if k in row}
  cases.append({"case_id":row.get("case_id") or hashlib.sha256(json.dumps(row,sort_keys=True,default=str).encode()).hexdigest(),
                "observed_at":observed,"features":feats,"outcomes":row.get("outcomes",{})})
 return {"revision":"OSI_036","current_observed_at":current["observed_at"],"feature_names":list(FEATURES),
         "comparable_cases":cases,"case_count":len(cases),"future_data_excluded":True,
         "execution_authority":False,"read_only":True}
