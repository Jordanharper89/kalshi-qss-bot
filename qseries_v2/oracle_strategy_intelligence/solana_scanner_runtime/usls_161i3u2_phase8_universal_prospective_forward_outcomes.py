from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161g4u2_phase8_live_certified_economics_producer_bridge import run as live_run

FREEZE="runtime_state/solana_opportunities/solana_scanner/phase8_universal_prospective_freezes_v2.json"

def run(root):
 root=Path(root)
 f=json.loads((root/FREEZE).read_text(encoding="utf-8"))
 time.sleep(5)
 live=live_run(root)
 rows=[x for x in live.get("rows",[])
       if x.get("market_address") is not None
       and isinstance(x.get("effective_price"),(int,float))
       and isinstance(x.get("observed_unix"),(int,float))]
 by={}
 for x in rows:
  by.setdefault((x["family"],str(x["market_address"])),[]).append(x)
 cases=[]
 for s in f.get("frozen_setups",[]):
  key=(s["family"],str(s["market_address"]))
  xs=[x for x in by.get(key,[]) if x["observed_unix"]>s["freeze_unix"]]
  if not xs:continue
  x=min(xs,key=lambda z:z["observed_unix"])
  p0=float(s["last_price"]);p1=float(x["effective_price"])
  cases.append({"freeze_hash":s["freeze_hash"],"family":s["family"],
   "market_address":s["market_address"],"freeze_unix":s["freeze_unix"],
   "later_observed_unix":x["observed_unix"],
   "entry_reference_price":p0,"later_price":p1,
   "gross_forward_return":p1/p0-1 if p0 else None,
   "entry_features":{"return_to_freeze":s.get("return_to_freeze"),
    "mfe_to_freeze":s.get("mfe_to_freeze"),"mae_to_freeze":s.get("mae_to_freeze"),
    "trade_count":s.get("trade_count"),"trade_velocity":s.get("trade_velocity")},
   "later_trade_signature":x.get("trade_signature"),"execution_authority":False})
 fams=sorted({x["family"] for x in cases})
 return {"revision":"USLS_161I3U2","source_live_revision":live.get("revision"),
  "prospective_case_count":len(cases),"family_count":len(fams),"families":fams,
  "cases":cases,
  "outcome_semantics":"STRICTLY_POST_FREEZE_SAME_FAMILY_SAME_MARKET_CERTIFIED_LIVE_PRICE",
  "next_boundary":"UNIVERSAL_EXPECTANCY_AND_FRICTION_GATE",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_universal_prospective_outcomes_v2.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
