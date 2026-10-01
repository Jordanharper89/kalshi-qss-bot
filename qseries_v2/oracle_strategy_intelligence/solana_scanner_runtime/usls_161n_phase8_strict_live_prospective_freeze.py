from __future__ import annotations
import hashlib,json,time
from pathlib import Path
SRC="runtime_state/solana_opportunities/solana_scanner/phase8_strict_live_direct_economics.json"
def run(root):
 root=Path(root);d=json.loads((root/SRC).read_text(encoding="utf-8"));groups={}
 for x in d.get("rows",[]):
  if not x.get("strict_live_provenance") or not x.get("market_address"):continue
  groups.setdefault((x["family"],str(x["market_address"]),x["input_asset"],x["output_asset"]),[]).append(x)
 freezes=[]
 for key,xs in groups.items():
  xs.sort(key=lambda z:z["observed_unix"]);prices=[float(z["effective_output_per_input"]) for z in xs]
  if not prices:continue
  fam,market,ia,oa=key;first,last=prices[0],prices[-1]
  f={"family":fam,"market_address":market,"input_asset":ia,"output_asset":oa,
     "freeze_unix":time.time(),"trade_count":len(xs),"first_price":first,"last_price":last,
     "return_to_freeze":last/first-1 if first else None,
     "mfe_to_freeze":max(prices)/first-1 if first else None,"mae_to_freeze":min(prices)/first-1 if first else None,
     "source_signatures":[z["trade_signature"] for z in xs],"future_outcome":None,
     "future_data_allowed_at_freeze":False,"execution_authority":False}
  f["freeze_hash"]=hashlib.sha256(json.dumps(f,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
  freezes.append(f)
 fams=sorted({x["family"] for x in freezes})
 return {"revision":"USLS_161N","frozen_setup_count":len(freezes),"families":fams,"frozen_setups":freezes,
  "orientation_rule":"SAME_MARKET_SAME_DIRECTED_ASSET_PAIR_ONLY",
  "next_boundary":"STRICTLY_LATER_DIRECT_ECONOMICS_OUTCOME_AND_EXPECTANCY",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=run(root);p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_strict_live_prospective_freezes.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
