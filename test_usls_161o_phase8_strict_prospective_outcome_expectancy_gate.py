import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161o_phase8_strict_prospective_outcome_expectancy_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"prospective_case_count":d["prospective_case_count"],
   "prospective_families":d["prospective_families"],"mean_gross_forward_return":d["mean_gross_forward_return"],
   "net_case_count":d["net_case_count"],"net_friction_families":d["net_friction_families"],
   "mean_net_forward_return":d["mean_net_forward_return"],"profitability_decision":d["profitability_decision"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["prospective_case_count"],0,"NO_STRICTLY_LATER_SAME_MARKET_SAME_PAIR_PROSPECTIVE_CASES")
  self.assertFalse(d["universal_phase8_complete"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161O strict prospective outcome + expectancy gate")
  print("[PASS] forward returns use only strictly later same-market same-directed-pair live economics")
  print("[PASS] net expectancy only where physical friction evidence exists")
  print("[STATE]",d["profitability_decision"])
if __name__=="__main__":unittest.main()
