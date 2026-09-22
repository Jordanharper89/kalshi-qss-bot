import unittest
from qseries_v2.oracle_pre_settlement_coverage.opc_012_coverage_priority_engine import verify_opc_012_coverage_priority_engine
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_opc_012_coverage_priority_engine())
if __name__=="__main__":
    print("="*72); print(" OPC-012 CERTIFICATION TEST"); print(" COVERAGE PRIORITY ENGINE"); print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OPC-012 certified"); print("[DONE] OPC-012 CERTIFIED")
