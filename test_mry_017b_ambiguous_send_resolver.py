import ast,unittest
from pathlib import Path
P=Path("qseries_v2/oracle_execution/solana_atomic_executor/mry_017b_ambiguous_send_resolver.py")
class T(unittest.TestCase):
 def test_source(self):
  s=P.read_text(encoding="utf-8");ast.parse(s)
  self.assertIn("getSignaturesForAddress",s)
  self.assertIn("SEND_AMBIGUOUS_HOLD",s)
  self.assertIn("send_attempted\"]=False",s)
  self.assertIn("age<120",s)
if __name__=="__main__":unittest.main(verbosity=2)
