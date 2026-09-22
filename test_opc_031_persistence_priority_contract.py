import unittest
from qseries_v2.oracle_pre_settlement_coverage.opc_031_persistence_priority_contract import verify_opc_031_persistence_priority_contract

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_opc_031_persistence_priority_contract())

if __name__=="__main__":
    print("="*80)
    print(" OPC-031 CERTIFICATION TEST")
    print(" PERSISTENCE PRIORITY CONTRACT")
    print("="*80)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OPC-031 certified")
    print("[DONE] OPC-031 CERTIFIED")
