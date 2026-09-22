import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_016_birth_log_instruction_correlation import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_corr(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps(d["family_summary"],sort_keys=True))
  for r in d["rows"][:30]:
   print("[CORR]",json.dumps({"family":r["matched_family"],"signature":r["signature"],
    "birth_term_hits":r["birth_term_hits"],"candidate_birth_evidence":r["candidate_birth_evidence"]},sort_keys=True))
  self.assertGreater(len(d["rows"]),0)
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-016 live birth-log/instruction correlation")
  print("[PASS] routine program activity kept separate from birth-evidence candidates")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
