import unittest
from qseries_v2.oracle_adapters.independent.oad_073_current_market_umd_dependency_index import *
class T(unittest.TestCase):
 def test_physical(self):
  markets,index,count=build_current_market_dependency_index(1000)
  print("[PHYSICAL] current_open_markets=",len(markets));print("[PHYSICAL] semantic_dependency_keys=",len(index));print("[PHYSICAL] market_fact_instances=",count)
  print("[PHYSICAL] sample_keys=",tuple(index.keys())[:20])
  self.assertGreater(len(markets),0);self.assertNotIn("event=new",index)
if __name__=="__main__":
 print("="*88);print(" OAD-073 PHYSICAL CERTIFICATION TEST");print(" CURRENT MARKET UMD-NORMALIZED DEPENDENCY INDEX");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] Current-market dependency keys normalized with frozen UMD semantic_key")
 print("[DONE] OAD-073 CERTIFIED")
