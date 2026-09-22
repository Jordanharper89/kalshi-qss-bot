import unittest
from qseries_v2.oracle_pre_settlement_coverage.opc_018_bounded_continuous_coverage_runner import verify_opc_018_bounded_continuous_coverage_runner

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_opc_018_bounded_continuous_coverage_runner())

if __name__=="__main__":
    print("="*72)
    print(" OPC-018 CERTIFICATION TEST")
    print(" BOUNDED CONTINUOUS COVERAGE RUNNER")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OPC-018 certified")
    print("[DONE] OPC-018 CERTIFIED")
