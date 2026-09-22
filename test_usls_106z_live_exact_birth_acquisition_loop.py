import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106z_live_exact_birth_acquisition_loop import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT,cycles=3,seconds=12,max_hydrations=8)
  print("[STATE]",json.dumps({"cycles_completed":d["cycles_completed"],
   "exact_births_detected":d["exact_births_detected"],
   "exact_births_persisted_new":d["exact_births_persisted_new"],
   "total_exact_birth_records":d["total_exact_birth_records"],"state":d["state"]},sort_keys=True))
  for x in d["history"]:print("[CYCLE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["cycles_completed"],0)
  self.assertTrue(d["raw_admission_before_classification"])
  self.assertTrue(d["rate_safe_retry"])
  self.assertFalse(d["identity_materialization_certified"])
  self.assertFalse(d["lifecycle_join_certified"])
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106Z live exact-birth acquisition loop")
  if d["exact_births_detected"]:
   print("[READY] exact prospective birth captured; identity materialization next")
  else:
   print("[WAIT] no exact prospective birth in bounded live window; rerun later")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
