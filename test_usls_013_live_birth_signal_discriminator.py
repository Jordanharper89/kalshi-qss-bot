import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_013_live_birth_signal_discriminator import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_discriminator(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({k:d[k] for k in ("sample_count","probable_birth_count","possible_birth_count")},sort_keys=True))
  for r in d["rows"]:print("[EVENT]",json.dumps(r,sort_keys=True))
  self.assertGreater(d["sample_count"],0)
  print("[PASS] USLS-013 live birth-vs-routine-activity discriminator")
  print("[SCOPE] candidate semantics only; no non-Meteora pool identity claim yet")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
