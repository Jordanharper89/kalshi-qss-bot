import unittest
from qseries_v2.oracle_scientific_reasoning.osr_017_scenario_branching import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_017_scenario_construction_branch_reasoning())
    def test_deterministic(self):
        r=make_branch("r",None,1,"r");a=make_branch("a","r",1,"a")
        self.assertEqual(build_scenario_tree((r,a)).tree_hash,build_scenario_tree((a,r)).tree_hash)
    def test_missing_parent(self):
        with self.assertRaises(ValueError): build_scenario_tree((make_branch("a","x",1,"a"),))

if __name__=="__main__":
    print("="*72);print(" OSR-017 CERTIFICATION TEST");print(" SCENARIO CONSTRUCTION + BRANCH REASONING");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Deterministic scenario-tree branch reasoning certified")
    print("[DONE] OSR-017 CERTIFIED")
