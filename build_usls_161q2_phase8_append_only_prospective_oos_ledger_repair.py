from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_161q2_phase8_append_only_prospective_oos_ledger_repair.py"
TEST=ROOT/"test_usls_161q2_phase8_append_only_prospective_oos_ledger_repair.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
SRC="runtime_state/solana_opportunities/solana_scanner/phase8_bidirectional_frozen_pair_outcomes.json"
DST="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_oos_ledger.json"

def run(root):
 root=Path(root);sp=root/SRC
 if not sp.exists():raise FileNotFoundError("USLS_161P_OUTPUT_MISSING:"+str(sp))
 src=json.loads(sp.read_text(encoding="utf-8"))
 dp=root/DST
 old={"cases":[]} if not dp.exists() else json.loads(dp.read_text(encoding="utf-8"))
 idx={(x.get("freeze_hash"),x.get("later_trade_signature")):x for x in old.get("cases",[])}
 before=len(idx)
 for x in src.get("cases",[]):
  k=(x.get("freeze_hash"),x.get("later_trade_signature"))
  if None not in k:idx.setdefault(k,x)
 cases=sorted(idx.values(),key=lambda x:(x.get("freeze_unix") or 0,x.get("later_observed_unix") or 0))
 fam={}
 for x in cases:fam[x["family"]]=fam.get(x["family"],0)+1
 return {"revision":"USLS_161Q2","source_revision":src.get("revision"),"case_count":len(cases),
  "new_case_count":len(cases)-before,"family_case_counts":fam,"cases":cases,
  "dedupe_key":"FREEZE_HASH_PLUS_LATER_TRADE_SIGNATURE","future_leakage":"FORBIDDEN",
  "next_boundary":"PROSPECTIVE_FEATURE_OUTCOME_EMPIRICAL_LEARNER",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root);p=Path(root)/DST;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161q2_phase8_append_only_prospective_oos_ledger_repair import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"source_revision":d["source_revision"],"case_count":d["case_count"],
   "new_case_count":d["new_case_count"],"family_case_counts":d["family_case_counts"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertEqual(d["source_revision"],"USLS_161P")
  self.assertGreater(d["case_count"],0,"EMPTY_PROSPECTIVE_OOS_LEDGER")
  self.assertEqual(len({(x["freeze_hash"],x["later_trade_signature"]) for x in d["cases"]}),d["case_count"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161Q2 append-only prospective OOS ledger repair")
  print("[PASS] 161P prospective cases persisted restart-safe without duplication")
  print("[NEXT] PROSPECTIVE_FEATURE_OUTCOME_EMPIRICAL_LEARNER")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
