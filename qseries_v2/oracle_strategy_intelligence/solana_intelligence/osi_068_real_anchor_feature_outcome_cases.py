from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path

def _dt(s): return datetime.fromisoformat(str(s).replace("Z","+00:00"))

def _num(v):
 try:return None if v is None else float(v)
 except Exception:return None

def build(root):
 anchor=json.loads((root/"runtime_state/solana_opportunities/outcomes/fresh_prospective_anchor.json").read_text(encoding="utf-8"))
 outcomes=json.loads((root/"runtime_state/solana_opportunities/outcomes/verified_forward_outcomes.json").read_text(encoding="utf-8"))
 a_at=_dt(anchor["observed_at"])
 created=anchor.get("pair_created_at")
 pair_age=None
 if created is not None:
  try: pair_age=max(0.0,a_at.timestamp()-(float(created)/1000.0))
  except Exception: pair_age=None
 buys=_num(anchor.get("buys_h24"));sells=_num(anchor.get("sells_h24"))
 total=(buys or 0)+(sells or 0)
 imbalance=None if total<=0 else ((buys or 0)-(sells or 0))/total
 features={
  "price_usd":_num(anchor.get("price_usd")),"liquidity_usd":_num(anchor.get("liquidity_usd")),
  "volume_h24":_num(anchor.get("volume_h24")),"buys_h24":buys,"sells_h24":sells,
  "buy_sell_imbalance":imbalance,"market_cap":_num(anchor.get("market_cap")),
  "fdv":_num(anchor.get("fdv")),"pair_age_seconds":pair_age,"dex_id":anchor.get("dex_id"),
 }
 cases=[]
 for o in outcomes.get("outcomes",[]):
  cases.append({"experience_id":o["experience_id"],"token_address":o["token_address"],"pair_address":o["pair_address"],
   "horizon_seconds":int(o["horizon_seconds"]),"feature_observed_at":anchor["observed_at"],
   "outcome_at":o["outcome_at"],"features":features,"return_fraction":float(o["return_fraction"]),
   "outcome_class":o["outcome_class"],"verified":bool(o["verified"]),"execution_authority":False})
 return {"revision":"OSI_068","case_count":len(cases),"cases":cases,"execution_authority":False}

def write(root):
 d=build(root);p=root/"runtime_state/solana_opportunities/learning/real_feature_outcome_cases.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
