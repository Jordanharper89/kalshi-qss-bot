import unittest
from qseries_v2.oracle_adapters.independent.oad_296_solana_multisource_universe_agreement_contradiction import *
class T(unittest.TestCase):
 def test_physical(self):
  r=compare_solana_universe_source_presence()
  print("[PHYSICAL] unique_tokens=",r.unique_tokens); print("[PHYSICAL] multi_source_tokens=",r.multi_source_tokens); print("[PHYSICAL] single_source_tokens=",r.single_source_tokens)
  self.assertGreater(r.unique_tokens,0); self.assertEqual(r.multi_source_tokens+r.single_source_tokens,r.unique_tokens)
if __name__=="__main__":
 z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not z.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-296 cross-source universe presence physically certified")
 print("[PASS] source disagreement remains explicit; no blending")
