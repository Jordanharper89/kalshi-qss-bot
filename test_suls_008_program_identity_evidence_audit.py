import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_008_program_identity_evidence_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT);self.assertFalse(d["execution_authority"]);print("[EVIDENCE_FILES]",d["evidence_files"])
  for r in d["rows"][:40]:print("[PROGRAM_EVIDENCE]",json.dumps(r,sort_keys=True))
  if d["evidence_files"]==0:self.fail("NO_PROGRAM_IDENTITY_EVIDENCE")
  print("[PASS] SULS-008 program identity evidence audit")
if __name__=="__main__":unittest.main()
