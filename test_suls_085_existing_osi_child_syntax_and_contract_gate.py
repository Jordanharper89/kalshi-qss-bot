import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_085_existing_osi_child_syntax_and_contract_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  for k in ("syntax_ok","suls_imported","daemon_thread","existing_stop_contract","existing_intake_preserved","execution_authority_false"):
   if not d[k]:self.fail(k.upper()+"_FALSE")
  self.assertFalse(d["top_level_launcher_modified"])
  print("[PASS] SULS-085 OSI child syntax/contract gate")
if __name__=="__main__":unittest.main()
