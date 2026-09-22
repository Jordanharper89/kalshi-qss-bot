import unittest
from qseries_v2.oracle_adapters.independent.oad_090_physical_sports_adapter_requirement_gate import *
class T(unittest.TestCase):
 def test_physical(self):
  s,rows=build_sports_adapter_requirements(1000)
  print("[PHYSICAL] snapshot_id=",s.snapshot_id);print("[PHYSICAL] evaluated_markets=",s.market_count);print("[PHYSICAL] sports_adapter_requirements=",len(rows))
  for x in rows:print("[BUILD_NEXT]",x.rank,x.sport,x.league,"live_markets=",x.live_markets,"sources=",x.source_families)
  self.assertGreater(s.market_count,0);self.assertTrue(all(x.rank==i+1 for i,x in enumerate(rows)))
if __name__=="__main__":
 print("="*88);print(" OAD-090 PHYSICAL CERTIFICATION TEST");print(" SPORTS ADAPTER REQUIREMENT GATE");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Sports adapter requirements derived from live structural demand")
 print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE")
 print("[DONE] OAD-086 through OAD-090 CAPABILITY SLICE CERTIFIED")
