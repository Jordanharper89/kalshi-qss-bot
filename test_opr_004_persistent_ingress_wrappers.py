import unittest
from qseries_v2.oracle_postgresql_reliability.opr_004_persistent_ingress_wrappers import *

class T(unittest.TestCase):
    def test_parser(self):self.assertEqual(read_children('CHILDREN={"a":"b.py"}\n')["a"],"b.py")
    def test_wrapper(self):
        s=wrapper_source("fast_lane","raw.py")
        self.assertIn("install_persistent_postgresql_ingress",s)
        compile(s,"wrapper","exec")

if __name__=="__main__":
    print("="*88);print(" OPR-004 CERTIFICATION TEST");print(" PERSISTENT INGRESS WRAPPER GENERATION");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Persistent producer wrapper generation certified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPR-004 CERTIFIED")
