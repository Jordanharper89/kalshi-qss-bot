import unittest
from qseries_v2.oracle_pre_settlement_coverage.opc_029_adaptive_coverage_throughput_controller import verify_opc_029_adaptive_coverage_throughput_controller

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_opc_029_adaptive_coverage_throughput_controller())

if __name__=="__main__":
    print("="*80)
    print(" OPC-029 CERTIFICATION TEST")
    print(" ADAPTIVE COVERAGE THROUGHPUT CONTROLLER")
    print("="*80)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OPC-029 certified")
    print("[DONE] OPC-029 CERTIFIED")
