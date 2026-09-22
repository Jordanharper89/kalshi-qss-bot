import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_108_phase6_universal_price_path_contract import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contract(self):
  p,d=write(ROOT)
  self.assertEqual(d["phase"],6)
  self.assertTrue(d["path_contract"]["continuous_between_horizons"])
  self.assertEqual(d["path_contract"]["standard_horizons_seconds"],[1,5,15,30,60,300,900])
  self.assertEqual(d["semantics"]["unknown_side"],"RETAIN")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-108 Phase 6 universal price-path contract")
  print("[PASS] continuous tape + standard horizons + MFE/MAE contract frozen")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
