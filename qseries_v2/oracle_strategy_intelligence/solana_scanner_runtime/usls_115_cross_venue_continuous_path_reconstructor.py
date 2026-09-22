from __future__ import annotations
import json
from pathlib import Path
H=(1,5,15,30,60,300,900)

def run(root):
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/cross_venue_economic_rows.json"
 d=json.loads(p.read_text(encoding="utf-8"));groups={}
 for x in d.get("rows",[]):
  if x.get("effective_price") is None:continue
  k=(x["family"],x.get("token_address"),x.get("market_address"))
  groups.setdefault(k,[]).append(x)
 paths=[]
 for k,xs in groups.items():
  xs.sort(key=lambda z:(z.get("trade_slot") or 0,z.get("trade_observed_unix") or 0,str(z.get("trade_signature"))))
  p0=float(xs[0]["effective_price"]);prices=[float(x["effective_price"]) for x in xs]
  anchor=xs[0].get("trade_observed_unix");cp=[]
  for h in H:
   y=None
   if isinstance(anchor,(int,float)):
    for x in xs:
     if isinstance(x.get("trade_observed_unix"),(int,float)) and x["trade_observed_unix"]>=anchor+h:
      y=x;break
   cp.append({"horizon_seconds":h,"state":"OBSERVED" if y else "PENDING_OR_UNAVAILABLE",
    "price":None if y is None else y["effective_price"],
    "return_from_first_trade":None if y is None else float(y["effective_price"])/p0-1})
  paths.append({"family":k[0],"token_address":k[1],"market_address":k[2],
   "trade_count":len(xs),"first_price":p0,"last_price":prices[-1],"high_price":max(prices),
   "low_price":min(prices),"mfe":max(prices)/p0-1,"mae":min(prices)/p0-1,
   "volume_base":sum(float(x.get("base_quantity") or 0) for x in xs),
   "volume_quote":sum(float(x.get("quote_quantity") or 0) for x in xs),
   "price_path":[{"signature":x["trade_signature"],"slot":x.get("trade_slot"),
                  "observed_unix":x.get("trade_observed_unix"),"price":x["effective_price"]} for x in xs],
   "checkpoints":cp})
 by={}
 for x in paths:by[x["family"]]=by.get(x["family"],0)+1
 return {"revision":"USLS_115","path_count":len(paths),"family_path_counts":by,"paths":paths,
  "continuous_between_horizons":True,"profitability_claimed":False,
  "execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/cross_venue_continuous_price_paths.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
