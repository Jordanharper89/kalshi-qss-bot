import unittest
from qseries_v2.oracle_pre_settlement_coverage.opc_020_oracle_live_runtime_integration_gate import verify_opc_020_oracle_live_runtime_integration_gate

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_opc_020_oracle_live_runtime_integration_gate())

if __name__=="__main__":
    print("="*72)
    print(" OPC-020 CERTIFICATION TEST")
    print(" ORACLE LIVE RUNTIME INTEGRATION GATE")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OPC-020 certified")
    print("[DONE] OPC-020 CERTIFIED")
