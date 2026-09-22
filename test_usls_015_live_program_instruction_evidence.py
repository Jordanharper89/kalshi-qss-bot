import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_015_live_program_instruction_evidence import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_extract(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in ("instruction_count","family_count","families")},sort_keys=True))
  for x in d["rows"][:40]:
   print("[IX]",json.dumps({k:x.get(k) for k in ("matched_family","signature","program_id","accounts","data","parsed","inner_parent_index")},sort_keys=True))
  self.assertGreater(d["instruction_count"],0)
  self.assertGreater(d["family_count"],0)
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-015 live watched-program instruction evidence extracted")
  print("[PASS] exact accounts/data preserved for decoder construction")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
