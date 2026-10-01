from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_162c_phase8_extended_multi_cohort_oos_accumulator.py"
TEST=ROOT/"test_usls_162c_phase8_extended_multi_cohort_oos_accumulator.py"
MOD_TEXT=r"""from __future__ import annotations
import asyncio,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161z_phase8_damm_v1_live_decoder_extension import decode_live_trade_extended
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161o2_phase8_exact_frozen_market_outcome_follower import follow,rpc
FREEZE="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_freeze_ledger.json"
LEDGER="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_oos_ledger.json"
def orient(x,a,b):
 p=x.get("effective_output_per_input")
 if not isinstance(p,(int,float)) or p<=0:return None,None
 if x.get("input_asset")==a and x.get("output_asset")==b:return float(p),"SAME_DIRECTION"
 if x.get("input_asset")==b and x.get("output_asset")==a:return 1/float(p),"REVERSED_AND_INVERTED"
 return None,None
def run(root,seconds=110,max_sigs=220):
 root=Path(root);setups=json.loads((root/FREEZE).read_text(encoding="utf-8")).get("frozen_setups",[])
 old={"cases":[]} if not (root/LEDGER).exists() else json.loads((root/LEDGER).read_text(encoding="utf-8"))
 idx={(x.get("freeze_hash"),x.get("later_trade_signature")):x for x in old.get("cases",[])}
 resolved={x.get("freeze_hash") for x in old.get("cases",[])};pending=[s for s in setups if s.get("freeze_hash") not in resolved]
 uniq=[];seen=set()
 for s in pending:
  k=(s["family"],str(s["market_address"]))
  if k not in seen:seen.add(k);uniq.append({"family":s["family"],"market_address":str(s["market_address"])})
 hits=asyncio.run(follow(uniq,seconds=seconds,max_sigs=max_sigs)) if uniq else [];dec=[];hydrated=0
 for h in hits:
  tx=rpc(h["signature"])
  if not isinstance(tx,dict):continue
  hydrated+=1
  for z in decode_live_trade_extended(h["family"],h["signature"],tx,h["observed_unix"]):
   if z.get("trade_signature")==h["signature"] and z.get("strict_live_provenance") and str(z.get("market_address"))==h["market_address"]:dec.append(z)
 by={}
 for z in dec:by.setdefault((z["family"],str(z["market_address"])),[]).append(z)
 added=0
 for s in pending:
  cand=[]
  for x in by.get((s["family"],str(s["market_address"])),[]):
   if x["observed_unix"]<=s["freeze_unix"]:continue
   p,mode=orient(x,s["input_asset"],s["output_asset"])
   if p is not None:cand.append((x,p,mode))
  if not cand:continue
  x,p1,mode=min(cand,key=lambda q:q[0]["observed_unix"]);p0=float(s["last_price"])
  c={"freeze_hash":s["freeze_hash"],"family":s["family"],"market_address":s["market_address"],"input_asset":s["input_asset"],"output_asset":s["output_asset"],
   "freeze_unix":s["freeze_unix"],"later_observed_unix":x["observed_unix"],"later_trade_signature":x["trade_signature"],
   "entry_reference_price":p0,"later_price_in_frozen_orientation":p1,"later_pair_mode":mode,
   "gross_forward_return":p1/p0-1 if p0 else None,"execution_authority":False}
  k=(c["freeze_hash"],c["later_trade_signature"])
  if k not in idx:idx[k]=c;added+=1
 rows=sorted(idx.values(),key=lambda x:(x.get("freeze_unix") or 0,x.get("later_observed_unix") or 0));fam={}
 for x in rows:fam[x["family"]]=fam.get(x["family"],0)+1
 return {"revision":"USLS_162C","pending_freeze_count":len(pending),"followed_market_count":len(uniq),"market_subscription_hit_count":len(hits),
  "hydrated_transaction_count":hydrated,"strict_same_market_decoded_count":len(dec),"new_case_count":added,"case_count":len(rows),
  "family_case_counts":fam,"cases":rows,"next_boundary":"LINK_ONLY_PHYSICAL_FRICTION_AND_RECHECK_PHASE8",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=run(root);p=Path(root)/LEDGER;p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162c_phase8_extended_multi_cohort_oos_accumulator import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"pending_freeze_count":d["pending_freeze_count"],"followed_market_count":d["followed_market_count"],
   "market_subscription_hit_count":d["market_subscription_hit_count"],"new_case_count":d["new_case_count"],"case_count":d["case_count"],
   "family_case_counts":d["family_case_counts"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["case_count"],0)
  self.assertGreater(d["new_case_count"],0,"NO_NEW_CASES_FROM_EXTENDED_COHORT")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-162C extended multi-cohort OOS accumulator")
  print("[NEXT] LINK_ONLY_PHYSICAL_FRICTION_AND_RECHECK_PHASE8")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
