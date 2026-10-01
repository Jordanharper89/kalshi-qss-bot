from __future__ import annotations
import json,time
from pathlib import Path

SOURCES=(
 "runtime_state/solana_opportunities/solana_scanner/phase8_pump_targeted_live_economics.json",
 "runtime_state/solana_opportunities/solana_scanner/phase8_gap_targeted_live_economics.json",
 "runtime_state/solana_opportunities/solana_scanner/pump_fun_strict_live_economics.json",
)
OUT="runtime_state/solana_opportunities/profitability_runtime/live_candidate_plays.json"

def _load(p):
 if not p.exists():return {}
 try:return json.loads(p.read_text(encoding="utf-8"))
 except Exception:return {}

def build(root,max_age_seconds=1800):
 root=Path(root);now=time.time();all_rows=[]
 for rel in SOURCES:
  d=_load(root/rel)
  for x in d.get("rows") or []:
   if not isinstance(x,dict):continue
   obs=x.get("observed_unix")
   if not isinstance(obs,(int,float)):continue
   if now-float(obs)>max_age_seconds:continue
   if not x.get("family") or not x.get("market_address"):continue
   if not isinstance(x.get("effective_output_per_input"),(int,float)):continue
   all_rows.append(x)
 groups={}
 for x in all_rows:
  key=(str(x["family"]),str(x["market_address"]),str(x.get("input_asset")),str(x.get("output_asset")))
  groups.setdefault(key,[]).append(x)
 plays=[]
 for (fam,mkt,ia,oa),rows in groups.items():
  rows.sort(key=lambda x:float(x["observed_unix"]))
  prices=[float(x["effective_output_per_input"]) for x in rows if float(x["effective_output_per_input"])>0]
  if not prices:continue
  first,last=prices[0],prices[-1];move=(last/first-1) if first else None
  sigs=[str(x.get("trade_signature")) for x in rows if x.get("trade_signature")]
  plays.append({"family":fam,"market_address":mkt,"input_asset":ia,"output_asset":oa,
   "first_observed_unix":float(rows[0]["observed_unix"]),"last_observed_unix":float(rows[-1]["observed_unix"]),
   "age_seconds":max(0.0,now-float(rows[-1]["observed_unix"])),"live_trade_count":len(rows),
   "first_observed_price":first,"current_observed_price":last,"current_capture_move":move,
   "latest_trade_signature":sigs[-1] if sigs else None,
   "candidate_state":"LIVE_CANDIDATE","execution_authority":False})
 plays.sort(key=lambda x:(x["last_observed_unix"],x["live_trade_count"]),reverse=True)
 return {"revision":"SSR_006","generated_unix":now,"candidate_count":len(plays),
  "max_age_seconds":max_age_seconds,"plays":plays,
  "semantics":"LIVE_DECODED_MARKET_CANDIDATES_NOT_TRADE_RECOMMENDATIONS",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
