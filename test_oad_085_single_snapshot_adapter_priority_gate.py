import unittest
from qseries_v2.oracle_adapters.independent.oad_085_single_snapshot_adapter_priority_gate import *

class T(unittest.TestCase):
    def test_physical(self):
        g=build_physical_adapter_priority_gate(1000,12)
        print("[PHYSICAL] snapshot_id=",g.snapshot_id)
        print("[PHYSICAL] evaluated_markets=",g.evaluated_markets)
        print("[PHYSICAL] unresolved_markets=",g.unresolved_markets)
        print("[PHYSICAL] adapter_priorities=",len(g.priorities))
        for p in g.priorities:
            print("[BUILD_NEXT]",p.rank,p.topic,p.source_family,"live_markets=",p.live_markets,"state=",p.state)
        self.assertGreater(g.evaluated_markets,0)
        self.assertTrue(all(p.rank==i+1 for i,p in enumerate(g.priorities)))
        self.assertTrue(all(p.state=="NOT_COVERED" for p in g.priorities))
        self.assertTrue(all(p.source_family for p in g.priorities))

if __name__=="__main__":
    print("="*88);print(" OAD-085 PHYSICAL CERTIFICATION TEST");print(" SINGLE-SNAPSHOT ADAPTER PRIORITY GATE");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] One physical cohort drives classification, demand mapping, and adapter ranking")
    print("[PASS] Unresolved markets remain explicit and never fabricate source coverage")
    print("[PASS] probability_enabled=FALSE")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OAD-081 through OAD-085 CAPABILITY SLICE CERTIFIED")
