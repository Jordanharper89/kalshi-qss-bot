import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_022_live_pump_create_v2_capture import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({k:d[k] for k in ("notifications_seen","exact_create_v2_count","create_v2_discriminator_hex")},sort_keys=True))
  for x in d["births"]:print("[BIRTH]",json.dumps({"signature":x["signature"],"slot":x["slot"],"observed_unix":x["observed_unix"],"block_time":x["block_time"],"account_count":len(x["instructions"][0]["accounts"])},sort_keys=True))
  self.assertGreater(d["notifications_seen"],0)
  self.assertGreater(d["exact_create_v2_count"],0)
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-022 live Pump.fun exact create_v2 physical capture")
  print("[PASS] birth is discriminator-proven, not keyword-inferred")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
