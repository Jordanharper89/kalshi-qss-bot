from __future__ import annotations
import hashlib,json
HORIZONS=(5,15,30,60,300,900)
EXECUTION_AUTHORITY=False

def _hash(x):
 return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def build_theses(bundle:dict,reasoning:dict,min_sources:int=2)->list[dict]:
 if bundle.get("source_count",0)<min_sources:return []
 out=[]
 for h in HORIZONS:
  meta=dict(reasoning.get("thesis_metadata") or {})
  family=meta.get("thesis_family")
  if family=="BUY_PRESSURE" and h==60:
   meta.update({"thesis_family":"BUY_PRESSURE","horizon_seconds":60,"target_return":0.10,"economic_stop_return":-0.05,"friction_bps":200})
  elif family=="BUY_PRESSURE":
   continue
  else:
   meta["horizon_seconds"]=h
   meta.setdefault("friction_bps",200)
  row={
   "opportunity_seed_id":bundle["opportunity_seed_id"],"asset_key":bundle["asset_key"],
   "freeze_at":bundle["freeze_at"],"horizon_seconds":h,"thesis_metadata":meta,
   "x_y_z_reasoning":dict(reasoning.get("x_y_z_reasoning") or {}),
   "historical_probability_claimed":False,"calibrated_probability":reasoning.get("calibrated_probability"),
   "paper_only":True,"prospective":True,"execution_authority":False
  }
  row["thesis_id"]=_hash(row);out.append(row)
 return out
