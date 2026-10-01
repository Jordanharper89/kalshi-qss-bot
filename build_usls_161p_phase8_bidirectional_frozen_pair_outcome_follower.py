from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_161p_phase8_bidirectional_frozen_pair_outcome_follower.py"
TEST=ROOT/"test_usls_161p_phase8_bidirectional_frozen_pair_outcome_follower.py"

MOD_TEXT=r"""from __future__ import annotations
import asyncio,json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161k_phase8_universal_live_economics_producer_rebuild import decode_live_trade
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161o2_phase8_exact_frozen_market_outcome_follower import follow,rpc

FREEZE="runtime_state/solana_opportunities/solana_scanner/phase8_strict_live_prospective_freezes.json"

def _orient(row,input_asset,output_asset):
 im=row.get("input_asset");om=row.get("output_asset");p=row.get("effective_output_per_input")
 if not isinstance(p,(int,float)) or p<=0:return None,None
 if im==input_asset and om==output_asset:return float(p),"SAME_DIRECTION"
 if im==output_asset and om==input_asset:return 1.0/float(p),"REVERSED_AND_INVERTED"
 return None,None

def run(root,seconds=90,max_sigs=120):
 root=Path(root);f=json.loads((root/FREEZE).read_text(encoding="utf-8"));setups=f.get("frozen_setups") or []
 unique=[];seen=set()
 for s in setups:
  k=(s["family"],str(s["market_address"]))
  if k not in seen:
   seen.add(k);unique.append({"family":s["family"],"market_address":str(s["market_address"])})
 hits=asyncio.run(follow(unique,seconds=seconds,max_sigs=max_sigs))
 decoded=[];hydrated=0
 for h in hits:
  tx=rpc(h["signature"])
  if not isinstance(tx,dict):continue
  hydrated+=1
  for z in decode_live_trade(h["family"],h["signature"],tx,h["observed_unix"]):
   if z.get("trade_signature")!=h["signature"] or not z.get("strict_live_provenance"):continue
   if str(z.get("market_address"))!=h["market_address"]:continue
   decoded.append(z)
 by={}
 for z in decoded:by.setdefault((z["family"],str(z["market_address"])),[]).append(z)
 cases=[]
 for s in setups:
  candidates=[]
  for x in by.get((s["family"],str(s["market_address"])),[]):
   if x["observed_unix"]<=s["freeze_unix"]:continue
   price,mode=_orient(x,s["input_asset"],s["output_asset"])
   if price is not None:candidates.append((x,price,mode))
  if not candidates:continue
  x,p1,mode=min(candidates,key=lambda q:q[0]["observed_unix"]);p0=float(s["last_price"])
  cases.append({"freeze_hash":s["freeze_hash"],"family":s["family"],"market_address":s["market_address"],
   "input_asset":s["input_asset"],"output_asset":s["output_asset"],"freeze_unix":s["freeze_unix"],
   "later_observed_unix":x["observed_unix"],"later_trade_signature":x["trade_signature"],
   "entry_reference_price":p0,"later_price_in_frozen_orientation":p1,
   "later_pair_mode":mode,"gross_forward_return":p1/p0-1 if p0 else None,
   "execution_authority":False})
 gv=[c["gross_forward_return"] for c in cases if isinstance(c.get("gross_forward_return"),(int,float))]
 return {"revision":"USLS_161P","frozen_market_count":len(unique),"frozen_setup_count":len(setups),
  "market_subscription_hit_count":len(hits),"hydrated_transaction_count":hydrated,
  "strict_same_market_decoded_count":len(decoded),"prospective_case_count":len(cases),
  "same_direction_case_count":sum(c["later_pair_mode"]=="SAME_DIRECTION" for c in cases),
  "reversed_inverted_case_count":sum(c["later_pair_mode"]=="REVERSED_AND_INVERTED" for c in cases),
  "prospective_families":sorted({c["family"] for c in cases}),
  "mean_gross_forward_return":None if not gv else sum(gv)/len(gv),
  "gross_positive_frequency":None if not gv else sum(v>0 for v in gv)/len(gv),
  "cases":cases,"orientation_policy":"LATER_REVERSE_TRADE_IS_INVERTED_INTO_FROZEN_PAIR_UNITS",
  "next_boundary":"APPEND_ONLY_PROSPECTIVE_OOS_LEDGER",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root);p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_bidirectional_frozen_pair_outcomes.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161p_phase8_bidirectional_frozen_pair_outcome_follower import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"frozen_market_count":d["frozen_market_count"],
   "market_subscription_hit_count":d["market_subscription_hit_count"],
   "strict_same_market_decoded_count":d["strict_same_market_decoded_count"],
   "prospective_case_count":d["prospective_case_count"],
   "same_direction_case_count":d["same_direction_case_count"],
   "reversed_inverted_case_count":d["reversed_inverted_case_count"],
   "prospective_families":d["prospective_families"],
   "mean_gross_forward_return":d["mean_gross_forward_return"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["market_subscription_hit_count"],0,"NO_POST_FREEZE_ACTIVITY_ON_FROZEN_MARKETS")
  self.assertGreater(d["prospective_case_count"],0,"NO_ORIENTATION_NORMALIZED_PROSPECTIVE_CASES")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161P bidirectional frozen-pair outcome follower")
  print("[PASS] opposite trade direction is inverted into the original frozen pair orientation")
  print("[NEXT] APPEND_ONLY_PROSPECTIVE_OOS_LEDGER")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
