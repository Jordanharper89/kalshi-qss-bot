import unittest
from qseries_v2.oracle_pre_settlement_coverage.opc_019_coverage_recovery_health_supervision import verify_opc_019_coverage_recovery_health_supervision

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_opc_019_coverage_recovery_health_supervision())

if __name__=="__main__":
    print("="*72)
    print(" OPC-019 CERTIFICATION TEST")
    print(" COVERAGE RECOVERY HEALTH SUPERVISION")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OPC-019 certified")
    print("[DONE] OPC-019 CERTIFIED")
