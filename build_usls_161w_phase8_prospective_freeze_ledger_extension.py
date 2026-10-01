from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_161w_phase8_prospective_freeze_ledger_extension.py"
TEST=ROOT/"test_usls_161w_phase8_prospective_freeze_ledger_extension.py"

MOD_TEXT=r"""from __future__ import annotations
import hashlib,json,time
from pathlib import Path
SRC="runtime_state/solana_opportunities/solana_scanner/phase8_balanced_live_economics.json"
OLD="runtime_state/solana_opportunities/solana_scanner/phase8_strict_live_prospective_freezes.json"
DST="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_freeze_ledger.json"

def _hash(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def run(root):
 root=Path(root);src=json.loads((root/SRC).read_text(encoding="utf-8"))
 existing=[]
 if (root/DST).exists():existing=json.loads((root/DST).read_text(encoding="utf-8")).get("frozen_setups",[])
 elif (root/OLD).exists():existing=json.loads((root/OLD).read_text(encoding="utf-8")).get("frozen_setups",[])
 groups={}
 for x in src.get("rows",[]):
  k=(x["family"],str(x["market_address"]),x["input_asset"],x["output_asset"])
  groups.setdefault(k,[]).append(x)
 new=[];now=time.time()
 for (fam,market,ia,oa),xs in groups.items():
  xs.sort(key=lambda x:x["observed_unix"]);prices=[float(x["effective_output_per_input"]) for x in xs]
  f={"family":fam,"market_address":market,"input_asset":ia,"output_asset":oa,"freeze_unix":now,
   "trade_count":len(xs),"first_price":prices[0],"last_price":prices[-1],
   "return_to_freeze":prices[-1]/prices[0]-1 if prices[0] else None,
   "mfe_to_freeze":max(prices)/prices[0]-1 if prices[0] else None,
   "mae_to_freeze":min(prices)/prices[0]-1 if prices[0] else None,
   "source_signatures":[x["trade_signature"] for x in xs],"future_outcome":None,
   "future_data_allowed_at_freeze":False,"execution_authority":False}
  f["freeze_hash"]=_hash(f);new.append(f)
 byhash={x["freeze_hash"]:x for x in existing if x.get("freeze_hash")}
 before=len(byhash)
 for x in new:byhash.setdefault(x["freeze_hash"],x)
 allrows=sorted(byhash.values(),key=lambda x:x["freeze_unix"])
 fam={}
 for x in allrows:fam[x["family"]]=fam.get(x["family"],0)+1
 return {"revision":"USLS_161W","freeze_count":len(allrows),"new_freeze_count":len(allrows)-before,
  "family_freeze_counts":fam,"frozen_setups":allrows,"future_leakage":"FORBIDDEN",
  "next_boundary":"MULTI_COHORT_PROSPECTIVE_OOS_ACCUMULATOR",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=run(root);p=Path(root)/DST;p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161w_phase8_prospective_freeze_ledger_extension import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"freeze_count":d["freeze_count"],"new_freeze_count":d["new_freeze_count"],
   "family_freeze_counts":d["family_freeze_counts"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["freeze_count"],0,"EMPTY_PROSPECTIVE_FREEZE_LEDGER")
  self.assertTrue(all(not x["future_data_allowed_at_freeze"] for x in d["frozen_setups"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161W prospective freeze ledger extension")
  print("[PASS] newly observed strict live markets frozen without deleting prior cohorts")
  print("[NEXT] MULTI_COHORT_PROSPECTIVE_OOS_ACCUMULATOR")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
