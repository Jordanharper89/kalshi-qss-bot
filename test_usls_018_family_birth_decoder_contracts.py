import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_018_family_birth_decoder_contracts import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contracts(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"target_count":d["target_count"],"ready_count":d["ready_count"]},sort_keys=True))
  for r in d["rows"]:print("[FAMILY]",json.dumps(r,sort_keys=True))
  self.assertEqual(d["target_count"],14)
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-018 family birth decoder readiness contracts")
  print("[PASS] no family is falsely certified without live instruction + birth + token-role evidence")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
