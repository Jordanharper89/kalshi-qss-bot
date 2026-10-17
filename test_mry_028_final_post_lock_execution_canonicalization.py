import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_final_order(self):
  s=R.read_text(); ast.parse(s)
  a=s.index("out=_mry019_align_meteora_programs(out)")
  b=s.index("out=_reverse_prepend_ata_readiness(",a)
  c=s.index("return out,old_bound,new_bound",b)
  self.assertLess(a,b); self.assertLess(b,c)
 def test_single_final_candidate_owner(self):
  s=R.read_text()
  start=s.index("def _fast_010_profit_lock_route")
  end=s.index("\ndef ",start+5)
  f=s[start:end]
  self.assertNotIn("_reverse_instruction_sets(",f)
  self.assertNotIn("candidate_instruction_sets(",f)
 def test_guards(self):
  s=R.read_text()
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
if __name__=="__main__":
 unittest.main(verbosity=2)
