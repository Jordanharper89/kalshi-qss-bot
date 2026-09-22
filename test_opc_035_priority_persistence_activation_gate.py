import unittest
from qseries_v2.oracle_pre_settlement_coverage.opc_035_priority_persistence_activation_gate import verify_opc_035_priority_persistence_activation_gate

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_opc_035_priority_persistence_activation_gate())

if __name__=="__main__":
    print("="*80)
    print(" OPC-035 CERTIFICATION TEST")
    print(" PRIORITY PERSISTENCE ACTIVATION GATE")
    print("="*80)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OPC-035 certified")
    print("[DONE] OPC-035 CERTIFIED")
