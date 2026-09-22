import unittest
from qseries_v2.oracle_pre_settlement_coverage.opc_032_cross_process_persistence_arbiter import verify_opc_032_cross_process_persistence_arbiter

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_opc_032_cross_process_persistence_arbiter())

if __name__=="__main__":
    print("="*80)
    print(" OPC-032 CERTIFICATION TEST")
    print(" CROSS PROCESS PERSISTENCE ARBITER")
    print("="*80)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OPC-032 certified")
    print("[DONE] OPC-032 CERTIFIED")
