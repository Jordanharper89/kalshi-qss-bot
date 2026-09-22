from __future__ import annotations
import json
from pathlib import Path

def repair(root):
 root=Path(root)
 p=root/"runtime_state/solana_opportunities/universal_launch_scanner/pump_marginal_prices.json"
 d=json.loads(p.read_text(encoding="utf-8"))
 rows=[]
 for x in d.get("rows") or []:
  vt=x.get("virtual_token_reserves") or 0
  vq=x.get("virtual_quote_reserves") or 0
  y=dict(x)
  if vt>0 and vq>0 and x.get("marginal_quote_per_token") is not None:
   y["price_state"]="PRICE_AVAILABLE"
   y["price_available"]=True
  else:
   y["marginal_quote_per_token"]=None
   y["price_state"]="PRICE_UNAVAILABLE_ZERO_RESERVES"
   y["price_available"]=False
  y["profitability_eligible"]=False
  y["execution_authority"]=False
  rows.append(y)
 out={"revision":"USLS_026B","row_count":len(rows),
  "price_available_count":sum(1 for x in rows if x["price_available"]),
  "price_unavailable_count":sum(1 for x in rows if not x["price_available"]),
  "rows":rows,"profitability_claimed":False,
  "execution_authority":False,"read_only":True}
 q=root/"runtime_state/solana_opportunities/universal_launch_scanner/pump_marginal_prices.json"
 q.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8")
 return q,out

def write(root): return repair(root)
