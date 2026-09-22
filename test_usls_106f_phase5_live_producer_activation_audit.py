import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_lifecycle.usls_106f_phase5_live_producer_activation_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"producer_count":d["producer_count"],
   "producer_paths_by_target":d["producer_paths_by_target"],
   "runtime_registration_hit_count":len(d["runtime_registration_hits"])},sort_keys=True))
  for x in d["producers"]:print("[PRODUCER]",json.dumps(x,sort_keys=True))
  for x in d["runtime_registration_hits"][:30]:print("[REGISTRATION]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["producer_count"],0,"NO_TARGET_PRODUCERS_FOUND")
  self.assertFalse(d["certification_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106F live producer activation audit")
  print("[PASS] no lifecycle certification claimed")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
