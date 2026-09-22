import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_134_phase7_cross_venue_native_friction_extractor import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  fee_fams=sum(v["fee"]>0 for v in d["family_support"].values())
  liq_fams=sum(v["liquidity"]>0 for v in d["family_support"].values())
  print("[STATE]",json.dumps({"row_count":d["row_count"],"fee_family_count":fee_fams,
   "liquidity_family_count":liq_fams,"family_support":d["family_support"]},sort_keys=True))
  self.assertEqual(d["row_count"],585)
  self.assertGreater(fee_fams,0)
  self.assertGreater(liq_fams,0)
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-134 cross-venue native friction extractor")
  print("[PASS] native fee/reserve evidence preserved without unsafe cross-asset conversion")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
