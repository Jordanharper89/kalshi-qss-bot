from __future__ import annotations
import json
from pathlib import Path

SRC="runtime_state/solana_opportunities/solana_scanner/cross_venue_economic_rows_repaired.json"
MAX_GAP_SECONDS=5.0

def run(root):
 d=json.loads((Path(root)/SRC).read_text(encoding="utf-8"))
 groups={}
 for x in d.get("rows",[]):
  if x.get("effective_price") is None:continue
  k=(x.get("family"),x.get("market_address"),x.get("asset_a"),x.get("asset_b"))
  groups.setdefault(k,[]).append(x)
 rows=[];fam={}
 for k,xs in groups.items():
  xs.sort(key=lambda x:(x.get("trade_observed_unix") or 0,x.get("trade_slot") or 0,str(x.get("trade_signature"))))
  prev=None
  for x in xs:
   now=x.get("trade_observed_unix");ref=None;gap=None;dev=None;state="NO_PRIOR_REFERENCE"
   if prev is not None:
    pt=prev.get("trade_observed_unix")
    if isinstance(now,(int,float)) and isinstance(pt,(int,float)):
     gap=float(now)-float(pt)
     if 0<=gap<=MAX_GAP_SECONDS:
      ref=float(prev["effective_price"])
      cur=float(x["effective_price"])
      dev=(cur/ref)-1 if ref else None
      state="BOUNDED_PRIOR_OBSERVED_REFERENCE"
    else:state="PRIOR_REFERENCE_OUTSIDE_GAP_BOUND"
   row={"family":k[0],"market_address":k[1],"asset_a":k[2],"asset_b":k[3],
    "trade_signature":x.get("trade_signature"),"trade_observed_unix":now,
    "effective_price":x.get("effective_price"),"pre_trade_reference_price":ref,
    "reference_gap_seconds":gap,"realized_execution_deviation_fraction":dev,
    "reference_state":state,"max_gap_seconds":MAX_GAP_SECONDS,
    "execution_authority":False}
   rows.append(row)
   z=fam.setdefault(k[0],{"rows":0,"bounded_reference":0})
   z["rows"]+=1;z["bounded_reference"]+=state=="BOUNDED_PRIOR_OBSERVED_REFERENCE"
   prev=x
 return {"revision":"USLS_129","row_count":len(rows),
  "bounded_reference_count":sum(x["reference_state"]=="BOUNDED_PRIOR_OBSERVED_REFERENCE" for x in rows),
  "family_support":fam,"rows":rows,
  "deviation_semantics":"REALIZED_EXECUTION_DEVIATION_VS_IMMEDIATELY_PRIOR_OBSERVED_TRADE_NOT_PURE_AMM_SLIPPAGE",
  "future_leakage":"FORBIDDEN","next_boundary":"PUMPSWAP_FEE_LIQUIDITY_NORMALIZATION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_pretrade_reference_execution_deviation.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
