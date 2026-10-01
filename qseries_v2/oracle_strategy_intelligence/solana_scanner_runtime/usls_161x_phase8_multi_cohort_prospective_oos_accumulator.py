from __future__ import annotations
import asyncio,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161k_phase8_universal_live_economics_producer_rebuild import decode_live_trade
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161o2_phase8_exact_frozen_market_outcome_follower import follow,rpc

FREEZE="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_freeze_ledger.json"
LEDGER="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_oos_ledger.json"

def _orient(x,a,b):
 p=x.get("effective_output_per_input")
 if not isinstance(p,(int,float)) or p<=0:return None,None
 if x.get("input_asset")==a and x.get("output_asset")==b:return float(p),"SAME_DIRECTION"
 if x.get("input_asset")==b and x.get("output_asset")==a:return 1/float(p),"REVERSED_AND_INVERTED"
 return None,None

def run(root,seconds=100,max_sigs=180):
 root=Path(root);f=json.loads((root/FREEZE).read_text(encoding="utf-8"));setups=f.get("frozen_setups") or []
 old={"cases":[]} if not (root/LEDGER).exists() else json.loads((root/LEDGER).read_text(encoding="utf-8"))
 existing={(x.get("freeze_hash"),x.get("later_trade_signature")):x for x in old.get("cases",[])}
 resolved={x.get("freeze_hash") for x in old.get("cases",[])}
 pending=[s for s in setups if s.get("freeze_hash") not in resolved]
 unique=[];seen=set()
 for s in pending:
  k=(s["family"],str(s["market_address"]))
  if k not in seen:seen.add(k);unique.append({"family":s["family"],"market_address":str(s["market_address"])})
 hits=asyncio.run(follow(unique,seconds=seconds,max_sigs=max_sigs)) if unique else []
 decoded=[];hydrated=0
 for h in hits:
  tx=rpc(h["signature"])
  if not isinstance(tx,dict):continue
  hydrated+=1
  for z in decode_live_trade(h["family"],h["signature"],tx,h["observed_unix"]):
   if z.get("trade_signature")==h["signature"] and z.get("strict_live_provenance") and str(z.get("market_address"))==h["market_address"]:
    decoded.append(z)
 by={}
 for z in decoded:by.setdefault((z["family"],str(z["market_address"])),[]).append(z)
 added=[]
 for s in pending:
  cand=[]
  for x in by.get((s["family"],str(s["market_address"])),[]):
   if x["observed_unix"]<=s["freeze_unix"]:continue
   p,mode=_orient(x,s["input_asset"],s["output_asset"])
   if p is not None:cand.append((x,p,mode))
  if not cand:continue
  x,p1,mode=min(cand,key=lambda q:q[0]["observed_unix"]);p0=float(s["last_price"])
  c={"freeze_hash":s["freeze_hash"],"family":s["family"],"market_address":s["market_address"],
   "input_asset":s["input_asset"],"output_asset":s["output_asset"],"freeze_unix":s["freeze_unix"],
   "later_observed_unix":x["observed_unix"],"later_trade_signature":x["trade_signature"],
   "entry_reference_price":p0,"later_price_in_frozen_orientation":p1,"later_pair_mode":mode,
   "gross_forward_return":p1/p0-1 if p0 else None,"execution_authority":False}
  k=(c["freeze_hash"],c["later_trade_signature"])
  if k not in existing:existing[k]=c;added.append(c)
 cases=sorted(existing.values(),key=lambda x:(x.get("freeze_unix") or 0,x.get("later_observed_unix") or 0))
 fam={}
 for x in cases:fam[x["family"]]=fam.get(x["family"],0)+1
 return {"revision":"USLS_161X","pending_freeze_count":len(pending),"followed_market_count":len(unique),
  "market_subscription_hit_count":len(hits),"hydrated_transaction_count":hydrated,
  "strict_same_market_decoded_count":len(decoded),"new_case_count":len(added),"case_count":len(cases),
  "family_case_counts":fam,"cases":cases,"next_boundary":"UPDATED_PHASE8_LEARNING_AND_COVERAGE_CHECKPOINT",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root);p=Path(root)/LEDGER;p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
