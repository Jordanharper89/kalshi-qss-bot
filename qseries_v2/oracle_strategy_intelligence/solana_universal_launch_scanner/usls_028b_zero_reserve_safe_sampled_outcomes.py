from __future__ import annotations
import json
from pathlib import Path

def _raw_price(s):
 vt=(s or {}).get("virtual_token_reserves") or 0
 vq=(s or {}).get("virtual_quote_reserves") or 0
 return (vq/vt) if vt>0 and vq>0 else None

def resolve(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 d=json.loads((base/"pump_short_horizon_curve_follow.json").read_text(encoding="utf-8"))
 pts=[]
 for x in d["samples"]:
  p=_raw_price(x["state"])
  pts.append({"horizon_seconds":x["horizon_seconds"],"price_ratio_raw":p,
   "price_state":"PRICE_AVAILABLE" if p is not None else "PRICE_UNAVAILABLE_ZERO_RESERVES",
   "target_unix":x["target_unix"],"observed_unix":x["observed_unix"],
   "lag_seconds":x.get("lag_seconds",0.0),"return_from_anchor":None})
 anchor_row=next((x for x in pts if x["price_ratio_raw"] is not None),None)
 if anchor_row:
  anchor=anchor_row["price_ratio_raw"]
  for x in pts:
   if x["price_ratio_raw"] is not None:
    x["return_from_anchor"]=x["price_ratio_raw"]/anchor-1.0
 rets=[x["return_from_anchor"] for x in pts if x["return_from_anchor"] is not None]
 return {"revision":"USLS_028B","signature":d["signature"],"token_address":d["token_address"],
  "quote_mint":d["quote_mint"],"points":pts,
  "anchor_horizon_seconds":None if anchor_row is None else anchor_row["horizon_seconds"],
  "sampled_mfe":max(rets) if rets else None,"sampled_mae":min(rets) if rets else None,
  "price_available_count":sum(1 for x in pts if x["price_ratio_raw"] is not None),
  "price_unavailable_count":sum(1 for x in pts if x["price_ratio_raw"] is None),
  "semantics":"SAMPLED_BONDING_CURVE_PRICE_PATH_PRE_FEE_NOT_EXECUTABLE_PNL",
  "remaining_horizons":d["remaining_horizons"],"profitability_claimed":False,
  "execution_authority":False,"read_only":True}

def write(root):
 d=resolve(root);p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/pump_sampled_path_outcomes.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
