import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_lifecycle.usls_106e_phase5_prospective_delta_probe import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_probe(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"state":d["state"],"birth_baseline_count":d["birth_baseline_count"],
   "birth_current_count":d["birth_current_count"],"new_birth_count":d["new_birth_count"],
   "new_trade_count":d["new_trade_count"],
   "trade_sources":[{"path":x["path"],"baseline_count":x.get("baseline_count"),"current_count":x.get("current_count"),"new_count":x["new_count"]} for x in d["trade_sources"]]},sort_keys=True))
  self.assertGreaterEqual(d["birth_current_count"],d["birth_baseline_count"])
  self.assertTrue(all(x["new_count"]>=0 for x in d["trade_sources"]))
  self.assertFalse(d["certification_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106E prospective post-bootstrap delta probe")
  print("[PASS] no lifecycle join certification claimed")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
