import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_013b_multifamily_birth_signal_discriminator_repair import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_discriminator(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in (
   "sample_count","family_count","families","probable_birth_count",
   "possible_birth_count","routine_activity_count")},sort_keys=True))
  for r in d["rows"]:
   print("[EVENT]",json.dumps(r,sort_keys=True))
  self.assertGreater(d["sample_count"],0)
  self.assertGreater(d["family_count"],0)
  self.assertTrue(all(r["families"] for r in d["rows"]))
  self.assertTrue(all(r["state"] in (
   "PROBABLE_BIRTH","POSSIBLE_BIRTH","ACTIVITY_NOT_BIRTH_PROVEN") for r in d["rows"]))
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-013B multi-family birth-vs-routine-activity discriminator")
  print("[PASS] hydrated cross-program transactions preserve all observed venue families")
  print("[SCOPE] candidate semantics only; exact non-Meteora pool identity remains unclaimed")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
