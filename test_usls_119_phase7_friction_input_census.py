import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_119_phase7_friction_input_census import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  fams=len(d["family_signal_counts"])
  print("[STATE]",json.dumps({"artifact_count":d["artifact_count"],
   "family_count":fams,"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["artifact_count"],0,"NO_FRICTION_INPUT_ARTIFACTS_DISCOVERED")
  self.assertGreater(fams,0,"NO_FAMILY_FRICTION_INPUTS_DISCOVERED")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-119 Phase 7 friction input census")
  print("[PASS] fee/liquidity/latency/price/amount evidence inventoried")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
