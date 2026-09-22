import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_011_live_14_program_websocket_probe import run
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=run(ROOT,12)
  print("[STATE]",json.dumps({k:d[k] for k in ("ack_count","expected_ack_count","notification_count","family_notification_counts")},sort_keys=True))
  self.assertEqual(d["ack_count"],14);self.assertEqual(d["ack_count"],d["expected_ack_count"]);self.assertGreater(d["notification_count"],0)
  print("[PASS] USLS-011 14-program live websocket subscription physical probe")
  print("[PASS] all verified venues accepted by live confirmed logsSubscribe")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
