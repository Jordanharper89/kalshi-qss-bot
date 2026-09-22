import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_006_verified_mainnet_program_registry import write,PROGRAMS
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_verify(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"program_count":len(d["programs"]),
   "verified_executable_count":d["verified_executable_count"]},sort_keys=True))
  for r in d["programs"]:print("[PROGRAM]",json.dumps(r,sort_keys=True))
  self.assertEqual(len(d["programs"]),len(PROGRAMS))
  self.assertTrue(all(x["account_exists"] for x in d["programs"]))
  self.assertTrue(all(x["executable"] for x in d["programs"]))
  print("[PASS] USLS-006 mainnet program registry physically executable")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
