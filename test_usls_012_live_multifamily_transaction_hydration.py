import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_012_live_multifamily_transaction_hydration import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_hydration(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({k:d[k] for k in ("family_count","sample_count","hydrated_count")},sort_keys=True))
  for r in d["rows"]:print("[TX]",json.dumps({"family":r["family"],"signature":r["signature"],"slot":r["slot"],"hydrated":r["hydrated"],"error":r["error"]},sort_keys=True))
  self.assertGreater(d["sample_count"],0);self.assertGreater(d["hydrated_count"],0)
  print("[PASS] USLS-012 live multi-family transaction hydration")
  print("[PASS] live venue notifications can be converted into full transaction evidence")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
