from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_162l_phase8_pump_targeted_freeze_extension.py"
TEST=ROOT/"test_usls_162l_phase8_pump_targeted_freeze_extension.py"

MOD_TEXT=r"""from __future__ import annotations
import hashlib,json,time
from pathlib import Path
SRC="runtime_state/solana_opportunities/solana_scanner/phase8_pump_targeted_live_economics.json"
DST="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_freeze_ledger.json"

def run(root):
 root=Path(root);src=json.loads((root/SRC).read_text(encoding="utf-8"))
 old=json.loads((root/DST).read_text(encoding="utf-8")) if (root/DST).exists() else {"frozen_setups":[]}
 groups={}
 for x in src.get("rows",[]):
  groups.setdefault((x["family"],str(x["market_address"]),x["input_asset"],x["output_asset"]),[]).append(x)
 idx={x["freeze_hash"]:x for x in old.get("frozen_setups",[]) if x.get("freeze_hash")};before=len(idx);now=time.time()
 for (fam,mkt,ia,oa),xs in groups.items():
  xs.sort(key=lambda x:x["observed_unix"]);ps=[float(x["effective_output_per_input"]) for x in xs]
  f={"family":fam,"market_address":mkt,"input_asset":ia,"output_asset":oa,"freeze_unix":now,
   "trade_count":len(xs),"first_price":ps[0],"last_price":ps[-1],
   "return_to_freeze":ps[-1]/ps[0]-1 if ps[0] else None,"mfe_to_freeze":max(ps)/ps[0]-1 if ps[0] else None,
   "mae_to_freeze":min(ps)/ps[0]-1 if ps[0] else None,"source_signatures":[x["trade_signature"] for x in xs],
   "future_outcome":None,"future_data_allowed_at_freeze":False,"execution_authority":False}
  f["freeze_hash"]=hashlib.sha256(json.dumps(f,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
  idx.setdefault(f["freeze_hash"],f)
 rows=sorted(idx.values(),key=lambda x:x["freeze_unix"])
 fam={}
 for x in rows:fam[x["family"]]=fam.get(x["family"],0)+1
 return {"revision":"USLS_162L","freeze_count":len(rows),"new_freeze_count":len(rows)-before,
  "family_freeze_counts":fam,"frozen_setups":rows,
  "pump_fun_freeze_count":fam.get("PUMP_FUN",0),"pumpswap_freeze_count":fam.get("PUMP_SWAP",0),
  "next_boundary":"ALL14_MULTI_COHORT_PROSPECTIVE_OOS_FOLLOWER",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root);p=Path(root)/DST;p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162l_phase8_pump_targeted_freeze_extension import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"freeze_count":d["freeze_count"],"new_freeze_count":d["new_freeze_count"],
   "pump_fun_freeze_count":d["pump_fun_freeze_count"],"pumpswap_freeze_count":d["pumpswap_freeze_count"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["new_freeze_count"],0,"NO_NEW_PUMP_TARGETED_FREEZES")
  self.assertGreater(d["pump_fun_freeze_count"],0,"PUMP_FUN_NOT_IN_FREEZE_LEDGER")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-162L Pump-targeted freeze extension")
  print("[NEXT] ALL14_MULTI_COHORT_PROSPECTIVE_OOS_FOLLOWER")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
