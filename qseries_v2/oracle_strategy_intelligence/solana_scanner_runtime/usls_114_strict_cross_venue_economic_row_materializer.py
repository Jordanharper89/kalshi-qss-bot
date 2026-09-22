from __future__ import annotations
import json,math
from pathlib import Path

CENSUS="runtime_state/solana_opportunities/solana_scanner/cross_venue_trade_artifact_schema_census.json"

ALIASES={
 "signature":("trade_signature","signature"),"token":("token_address","token","mint","base_mint","trade_mint"),
 "market":("market_address","pool_address","pool","curve","bonding_curve","amm"),
 "side":("side","trade_side"),"base":("base_quantity","base_amount","token_amount"),
 "quote":("quote_quantity","quote_amount","sol_amount"),"price":("effective_price","price","price_usd","execution_price"),
 "slot":("trade_slot","slot"),"time":("trade_observed_unix","observed_unix","received_unix","block_time")}

def _first(d,names):
 for k in names:
  v=d.get(k)
  if v not in (None,""):return v
 return None

def _walk(x,out):
 if isinstance(x,dict):
  out.append(x)
  for v in x.values():_walk(v,out)
 elif isinstance(x,list):
  for v in x:_walk(v,out)

def _num(v):
 try:
  x=float(v)
  return x if math.isfinite(x) else None
 except Exception:return None

def _rows_for(root,path,family):
 p=Path(root)/path
 try:d=json.loads(p.read_text(encoding="utf-8"))
 except Exception:return []
 objs=[];_walk(d,objs);out=[]
 for o in objs:
  sig=_first(o,ALIASES["signature"]);token=_first(o,ALIASES["token"]);market=_first(o,ALIASES["market"])
  if not sig or not (token or market):continue
  base=_num(_first(o,ALIASES["base"]));quote=_num(_first(o,ALIASES["quote"]));price=_num(_first(o,ALIASES["price"]))
  method=None
  if price is not None and price>0:method="SOURCE_EXPLICIT_PRICE"
  elif base not in (None,0) and quote is not None:
   price=abs(quote/base);method="STRICT_QUOTE_OVER_BASE"
  else:continue
  out.append({"family":family,"token_address":token,"market_address":market,
   "trade_signature":sig,"trade_slot":_first(o,ALIASES["slot"]),
   "trade_observed_unix":_first(o,ALIASES["time"]),"side":_first(o,ALIASES["side"]) or "UNKNOWN",
   "base_quantity":base,"quote_quantity":quote,"effective_price":price,
   "price_method":method,"source_artifact":path,"execution_authority":False})
 return out

def run(root):
 c=json.loads((Path(root)/CENSUS).read_text(encoding="utf-8"));rows=[];by={}
 seen=set()
 for a in c.get("artifacts",[]):
  fam=a["family"]
  for x in _rows_for(root,a["path"],fam):
   key=(fam,x["trade_signature"],x.get("market_address"),x.get("token_address"))
   if key in seen:continue
   seen.add(key);rows.append(x);by[fam]=by.get(fam,0)+1
 return {"revision":"USLS_114","economic_row_count":len(rows),"family_row_counts":by,"rows":rows,
  "strict_no_guessed_identity":True,"quote_asset_policy":"AGNOSTIC",
  "price_semantics":"OBSERVED_EFFECTIVE_PRICE_NOT_EXECUTABLE_PNL",
  "next_boundary":"CROSS_VENUE_CONTINUOUS_PATH_RECONSTRUCTION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/cross_venue_economic_rows.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
