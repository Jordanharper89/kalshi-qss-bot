from __future__ import annotations
import json,math
from pathlib import Path

SRC="runtime_state/solana_opportunities/solana_scanner/cross_venue_continuous_price_paths_repaired.json"
H=(1,5,15,30,60,300,900)

def _finite(v):
 try:
  x=float(v)
  return x if math.isfinite(x) else None
 except Exception:return None

def run(root):
 d=json.loads((Path(root)/SRC).read_text(encoding="utf-8"))
 rows=[]
 for pi,p in enumerate(d.get("paths",[])):
  tape=p.get("price_path") or []
  timed=[x for x in tape if isinstance(x.get("observed_unix"),(int,float)) and _finite(x.get("price")) is not None]
  if not timed:continue
  timed.sort(key=lambda x:x["observed_unix"]);t0=timed[0]["observed_unix"];p0=float(timed[0]["price"])
  for h in H:
   cutoff=t0+h
   past=[x for x in timed if x["observed_unix"]<=cutoff]
   future=[x for x in timed if x["observed_unix"]>cutoff]
   if not past:continue
   prices=[float(x["price"]) for x in past]
   last=prices[-1]
   features={"trade_count_to_cutoff":len(past),
    "return_to_cutoff":last/p0-1 if p0 else None,
    "mfe_to_cutoff":max(prices)/p0-1 if p0 else None,
    "mae_to_cutoff":min(prices)/p0-1 if p0 else None,
    "last_price_at_cutoff":last}
   outcome=None
   if future:
    final=float(future[-1]["price"])
    outcome=final/last-1 if last else None
   rows.append({"case_id":f"USLS155-{pi:06d}-{h}",
    "family":p.get("family"),"market_address":p.get("market_address"),
    "asset_a":p.get("asset_a"),"asset_b":p.get("asset_b"),
    "prediction_horizon_seconds":h,"feature_cutoff_unix":cutoff,
    "features":features,"forward_observational_return":outcome,
    "future_rows_used_in_features":0,"execution_authority":False})
 return {"revision":"USLS_155","snapshot_count":len(rows),"snapshots":rows,
  "future_leakage":"FORBIDDEN","feature_time_rule":"ONLY_ROWS_AT_OR_BEFORE_CUTOFF",
  "next_boundary":"CROSS_LAUNCH_COMPARABLE_CASE_INDEX",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_leakage_safe_feature_snapshots.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
