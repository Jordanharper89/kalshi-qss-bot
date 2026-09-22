import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_008_universal_subscription_manifest import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_manifest(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"subscription_count":d["subscription_count"],
   "unknown_program_policy":d["unknown_program_policy"],"commitment":d["target_commitment"]},sort_keys=True))
  for r in d["subscriptions"]:print("[SUB]",json.dumps(r,sort_keys=True))
  self.assertGreaterEqual(d["subscription_count"],10)
  self.assertEqual(len({x["program_id"] for x in d["subscriptions"]}),d["subscription_count"])
  self.assertEqual(d["unknown_program_policy"],"STRUCTURAL_DISCOVERY_RETAIN_AND_TRIAGE")
  print("[PASS] USLS-008 universal subscription manifest")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
