import unittest
from qseries_v2.oracle_pre_settlement_coverage.opc_034_coverage_microbatch_yield_policy import verify_opc_034_coverage_microbatch_yield_policy

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_opc_034_coverage_microbatch_yield_policy())

if __name__=="__main__":
    print("="*80)
    print(" OPC-034 CERTIFICATION TEST")
    print(" COVERAGE MICROBATCH YIELD POLICY")
    print("="*80)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OPC-034 certified")
    print("[DONE] OPC-034 CERTIFIED")
