import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106za_birth_priority_fair_dispatch_loop import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT,cycles=3,seconds=12,max_total=18)
  print("[STATE]",json.dumps({"cycles_completed":d["cycles_completed"],
   "exact_births_detected":d["exact_births_detected"],
   "total_exact_birth_records":d["total_exact_birth_records"],"state":d["state"]},sort_keys=True))
  for x in d["history"]:print("[CYCLE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["cycles_completed"],0)
  self.assertTrue(d["birth_hint_is_priority_only"])
  self.assertTrue(d["fair_family_dispatch"])
  self.assertTrue(any(sum(x["family_dispatch_counts"].values())>0 for x in d["history"]))
  self.assertFalse(d["identity_materialization_certified"])
  self.assertFalse(d["lifecycle_join_certified"])
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106ZA birth-priority fair-dispatch loop")
  if d["exact_births_detected"]:
   print("[READY] exact prospective birth captured; identity materialization next")
  else:
   print("[WAIT] fair verified dispatch completed; no exact birth in bounded window")
  print("[PASS] heuristic birth hints used only for priority, never certification")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
