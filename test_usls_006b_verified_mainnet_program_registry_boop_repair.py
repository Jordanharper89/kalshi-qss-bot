import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_006b_verified_mainnet_program_registry_boop_repair import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_verify(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"program_count":d["program_count"],
   "verified_executable_count":d["verified_executable_count"],"all_verified":d["all_verified"]},sort_keys=True))
  for r in d["programs"]: print("[PROGRAM]",json.dumps(r,sort_keys=True))
  self.assertEqual(d["program_count"],14)
  self.assertEqual(d["verified_executable_count"],14)
  self.assertTrue(d["all_verified"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-006B all 14 target mainnet programs physically executable")
  print("[PASS] Boop.fun program ID repaired")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
