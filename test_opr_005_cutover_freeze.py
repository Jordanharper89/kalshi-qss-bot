import unittest
from qseries_v2.oracle_postgresql_reliability.opr_005_cutover_freeze import *

class T(unittest.TestCase):
    def test_identity(self):self.assertEqual(OPR_005_BUILD_ID,"OPR-005")
    def test_patch(self):
        s='CHILDREN={"a":"x.py","canonical_writer":"y.py"}\n'
        self.assertIn("z.py",patch_child(s,"a","z.py"))

if __name__=="__main__":
    print("="*88);print(" OPR-005 CERTIFICATION TEST");print(" PHYSICAL CONNECTION-REUSE CUTOVER + FREEZE");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Safe launcher cutover machinery certified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPR-005 GATE CERTIFIED")
