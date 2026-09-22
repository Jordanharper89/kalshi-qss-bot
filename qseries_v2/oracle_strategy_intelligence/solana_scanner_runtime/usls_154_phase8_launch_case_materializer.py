from __future__ import annotations
import json
from pathlib import Path

PATHS="runtime_state/solana_opportunities/solana_scanner/cross_venue_continuous_price_paths_repaired.json"

def run(root):
 root=Path(root)
 d=json.loads((root/PATHS).read_text(encoding="utf-8"))
 rows=[]
 for i,x in enumerate(d.get("paths",[])):
  first=x.get("first_price");last=x.get("last_price")
  if first in (None,0) or last is None:continue
  rows.append({
   "case_id":f"USLS154-{i:06d}",
   "family":x.get("family"),"market_address":x.get("market_address"),
   "asset_a":x.get("asset_a"),"asset_b":x.get("asset_b"),
   "trade_count":x.get("trade_count",0),
   "first_price":first,"last_price":last,
   "high_price":x.get("high_price"),"low_price":x.get("low_price"),
   "mfe":x.get("mfe"),"mae":x.get("mae"),
   "volume_base":x.get("volume_base"),"volume_quote":x.get("volume_quote"),
   "checkpoint_count":len(x.get("checkpoints") or []),
   "price_path_count":len(x.get("price_path") or []),
   "observational_return":float(last)/float(first)-1,
   "execution_supported":False,
   "execution_authority":False})
 by={}
 for x in rows:by[x["family"]]=by.get(x["family"],0)+1
 return {"revision":"USLS_154","case_count":len(rows),"family_case_counts":by,
  "cases":rows,"case_semantics":"OBSERVATIONAL_CROSS_LAUNCH_CASES_NOT_EXECUTABLE_PNL",
  "next_boundary":"LEAKAGE_SAFE_FEATURE_SNAPSHOT_EXTRACTION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_launch_cases.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
