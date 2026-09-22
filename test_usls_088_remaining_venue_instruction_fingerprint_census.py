import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_088_remaining_venue_instruction_fingerprint_census import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_census(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"fingerprint_count":d["fingerprint_count"]},sort_keys=True))
  for x in d["rows"][:40]:print("[FINGERPRINT]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["fingerprint_count"],0,"NO_PROGRAM_INSTRUCTION_FINGERPRINTS")
  self.assertTrue(d["unknown_instruction_retention"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-088 physical instruction fingerprint census")
  print("[PASS] semantics remain UNKNOWN until source/live evidence proves them")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
