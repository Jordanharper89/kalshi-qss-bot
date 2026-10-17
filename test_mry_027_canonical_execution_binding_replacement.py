import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_meteora_binding(self):
  s=R.read_text(); ast.parse(s)
  self.assertIn("tx=str(fixed[6][0])",s)
  self.assertIn('ac[11]["pubkey"]=tp',s)
  self.assertIn("candidate_instruction_sets",s)
 def test_reverse_compatibility(self):
  s=R.read_text()
  self.assertIn("def _reverse_prepend_ata_readiness(user,token,route=None)",s)
  self.assertIn("route=token",s)
 def test_guards(self):
  s=R.read_text()
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
if __name__=="__main__": unittest.main(verbosity=2)
