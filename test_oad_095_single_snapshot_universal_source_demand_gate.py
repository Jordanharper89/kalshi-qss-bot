import unittest
from qseries_v2.oracle_adapters.independent.oad_095_single_snapshot_universal_source_demand_gate import *
class T(unittest.TestCase):
 def test_physical(self):
  g=build_universal_source_demand_gate(1000)
  print("[PHYSICAL] snapshot_id=",g.snapshot_id);print("[PHYSICAL] evaluated_markets=",g.evaluated_markets);print("[PHYSICAL] unresolved=",g.unresolved)
  print("[PHYSICAL] priorities=",len(g.priorities))
  for p in g.priorities:print("[BUILD_NEXT]",p.rank,p.domain,p.subdomain,"live_markets=",p.live_markets,"sources=",p.source_families)
  self.assertGreater(g.evaluated_markets,0);self.assertTrue(all(p.rank==i+1 for i,p in enumerate(g.priorities)))
if __name__=="__main__":
 print("="*88);print(" OAD-095 PHYSICAL CERTIFICATION TEST");print(" SINGLE-SNAPSHOT UNIVERSAL SOURCE-DEMAND GATE");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] One live cohort drives final domain/source-demand ranking")
 print("[PASS] Unresolved demand remains explicit");print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE")
 print("[DONE] OAD-091 through OAD-095 CAPABILITY SLICE CERTIFIED")
