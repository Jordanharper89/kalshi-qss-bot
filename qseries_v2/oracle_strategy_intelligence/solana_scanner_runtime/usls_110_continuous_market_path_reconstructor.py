from __future__ import annotations
import json,time
from pathlib import Path
H=(1,5,15,30,60,300,900)

def run(root):
 src=Path(root)/"runtime_state/solana_opportunities/solana_scanner/pump_exact_trade_economic_path.json"
 d=json.loads(src.read_text(encoding="utf-8"))
 rows=[x for x in d.get("rows",[]) if x.get("effective_price") is not None]
 groups={}
 for x in rows:
  k=(x["family"],x["token_address"],x["market_address"],x.get("birth_signature"))
  groups.setdefault(k,[]).append(x)
 paths=[]
 for k,xs in groups.items():
  xs.sort(key=lambda x:(x.get("trade_slot") or 0,x.get("trade_observed_unix") or 0))
  p0=xs[0]["effective_price"];prices=[x["effective_price"] for x in xs]
  anchor=xs[0].get("trade_observed_unix")
  checkpoints=[]
  for h in H:
   eligible=[x for x in xs if anchor is not None and x.get("trade_observed_unix") is not None and x["trade_observed_unix"]>=anchor+h]
   y=eligible[0] if eligible else None
   checkpoints.append({"horizon_seconds":h,"state":"OBSERVED" if y else "PENDING_OR_UNAVAILABLE",
    "price":None if y is None else y["effective_price"],
    "return_from_first_trade":None if y is None else y["effective_price"]/p0-1})
  paths.append({"market_key":"|".join(map(str,k[:3])),"family":k[0],"token_address":k[1],"market_address":k[2],
   "birth_signature":k[3],"first_trade_price":p0,"last_price":prices[-1],
   "high_price":max(prices),"low_price":min(prices),"trade_count":len(xs),
   "mfe":max(prices)/p0-1,"mae":min(prices)/p0-1,
   "volume_base":sum(x.get("base_quantity") or 0 for x in xs),
   "volume_quote":sum(x.get("quote_quantity") or 0 for x in xs),
   "buy_count":sum(str(x.get("side")).upper()=="BUY" for x in xs),
   "sell_count":sum(str(x.get("side")).upper()=="SELL" for x in xs),
   "unknown_side_count":sum(str(x.get("side")).upper() not in ("BUY","SELL") for x in xs),
   "price_path":[{"slot":x.get("trade_slot"),"observed_unix":x.get("trade_observed_unix"),
                  "price":x["effective_price"],"trade_signature":x.get("trade_signature")} for x in xs],
   "checkpoints":checkpoints,
   "freshness_seconds":None if xs[-1].get("trade_observed_unix") is None else max(0,time.time()-xs[-1]["trade_observed_unix"])})
 return {"revision":"USLS_110","path_count":len(paths),
  "total_priced_trades":sum(x["trade_count"] for x in paths),"paths":paths,
  "continuous_between_horizons":True,"profitability_claimed":False,
  "execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/continuous_market_price_paths.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
