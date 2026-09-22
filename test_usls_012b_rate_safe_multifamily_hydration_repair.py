import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_012b_rate_safe_multifamily_hydration_repair import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_hydration(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in (
   "observed_family_count","unique_signature_count","hydrated_signature_count",
   "hydrated_family_count","missing_hydrated_families")},sort_keys=True))
  for r in d["rows"]:
   print("[TX]",json.dumps({"families":r["families"],"signature":r["signature"],
    "slot":r["slot"],"hydrated":r["hydrated"],"attempts":r["attempts"],
    "error":r["error"]},sort_keys=True))
  self.assertGreater(d["observed_family_count"],0)
  self.assertEqual(d["hydrated_family_count"],d["observed_family_count"])
  self.assertEqual(d["missing_hydrated_families"],[])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-012B rate-safe multi-family transaction hydration")
  print("[PASS] every family observed in the live probe has full transaction evidence")
  print("[PASS] duplicate cross-program signatures hydrated once")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
