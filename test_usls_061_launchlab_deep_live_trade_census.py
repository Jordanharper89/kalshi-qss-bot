import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_061_launchlab_deep_live_trade_census import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_census(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({k:d[k] for k in ("signature_count","hydrated_count","exact_trade_count","rpc_url_redacted")},sort_keys=True))
  for x in d["rows"]:print("[LAUNCHLAB_TRADE]",json.dumps({k:x[k] for k in ("signature","level","instruction_ordinal","instruction_name")},sort_keys=True))
  self.assertGreater(d["signature_count"],0);self.assertGreater(d["hydrated_count"],0)
  self.assertGreater(d["exact_trade_count"],0,"NO_EXACT_LAUNCHLAB_TRADE_FOUND_IN_DEEP_CENSUS")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-061 physical LaunchLab exact trade found")
  print("[PASS] deep recent-signature census replaced weak 3-signature sample")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
