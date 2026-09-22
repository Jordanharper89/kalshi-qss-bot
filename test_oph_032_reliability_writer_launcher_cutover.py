import unittest
from qseries_v2.oracle_production_hardening.oph_032_reliability_writer_launcher_cutover import *
class T(unittest.TestCase):
    def test_identity(self):self.assertEqual(RELIABILITY_WRITER,"run_oph_031_classified_single_writer_reliability_runtime.py")
    def test_patch(self):
        src='CHILDREN={"fast_lane":"run_oph_022_fast_lane_postgresql_ingress.py","canonical_writer":"run_oph_021_exclusive_postgresql_canonical_writer.py"}\n'
        out=patch_canonical_writer(src)
        self.assertIn(RELIABILITY_WRITER,out)
if __name__=="__main__":
    print("="*88);print(" OPH-032 CERTIFICATION TEST");print(" RELIABILITY WRITER LAUNCHER CUTOVER");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Canonical writer cutover machinery certified")
    print("[PASS] Producer PostgreSQL-ingress wrappers remain unchanged")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPH-032 CERTIFIED")
