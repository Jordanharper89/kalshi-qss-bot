import unittest
from qseries_v2.oracle_pre_settlement_coverage.opc_017_durable_coverage_runtime_state import verify_opc_017_durable_coverage_runtime_state

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_opc_017_durable_coverage_runtime_state())

if __name__=="__main__":
    print("="*72)
    print(" OPC-017 CERTIFICATION TEST")
    print(" DURABLE COVERAGE RUNTIME STATE")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OPC-017 certified")
    print("[DONE] OPC-017 CERTIFIED")
