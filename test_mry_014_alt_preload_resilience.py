import ast,unittest
from pathlib import Path
P=Path("qseries_v2/oracle_execution/solana_atomic_executor")
class T(unittest.TestCase):
 def test_activation(self):
  s=(P/"runtime.py").read_text(encoding="utf-8");ast.parse(s)
  self.assertIn("m14.preload(preload_canary_saved_alts,root)",s)
 def test_module(self):
  from qseries_v2.oracle_execution.solana_atomic_executor import mry_014_alt_preload_resilience as m
  self.assertTrue(callable(m.preload))
if __name__=="__main__":unittest.main(verbosity=2)
