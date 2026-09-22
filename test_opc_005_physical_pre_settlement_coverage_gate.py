import unittest
from qseries_v2.oracle_pre_settlement_coverage.opc_005_physical_pre_settlement_coverage_gate import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_opc_005_physical_pre_settlement_coverage_gate())

if __name__=="__main__":
    print("="*72)
    print(" OPC-005 CERTIFICATION TEST")
    print(" PHYSICAL PRE-SETTLEMENT COVERAGE GATE")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OPC-001 through OPC-005 live coverage measurement certified")
    print("[DONE] OPC-005 CERTIFIED")
