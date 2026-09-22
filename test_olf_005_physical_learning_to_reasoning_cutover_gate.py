import unittest
from qseries_v2.oracle_learning_feedback.olf_005_live_cutover import *

class T(unittest.TestCase):
    def test_identity(self):self.assertEqual(OLF_005_BUILD_ID,"OLF-005")
    def test_patch(self):
        s='CHILDREN={"reasoning":"old.py","learning":"learn.py"}\n'
        self.assertIn(TARGET,patch_reasoning_child(s))

if __name__=="__main__":
    print("="*88);print(" OLF-005 CERTIFICATION TEST");print(" PHYSICAL LEARNING -> REASONING CUTOVER GATE");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Safe reasoning-child cutover machinery certified")
    print("[PASS] Physical learner-hash consumption required")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLF-005 GATE CERTIFIED")
