import unittest
from qseries_v2.oracle_pre_settlement_coverage.opc_024_supervised_24x7_coverage_runtime import CoverageLoadBudget,run_one_supervised_coverage_cycle,verify_opc_024_supervised_24x7_coverage_runtime
class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_opc_024_supervised_24x7_coverage_runtime())
    def test_retry_exhaustion_nonfatal(self):
        def cycle(root,budget=None,progress=None):
            class PostgreSQLPersistenceRoutingFailure(Exception): pass
            raise PostgreSQLPersistenceRoutingFailure("PostgreSQL batch append was not committed")
        r=run_one_supervised_coverage_cycle(".",CoverageLoadBudget(),cycle_fn=cycle,sleep_fn=lambda s:None,max_retries=2)
        self.assertEqual(r.status,"TRANSIENT_FAILURE")
        self.assertTrue(r.exhausted)
    def test_programming_error_fatal(self):
        def cycle(root,budget=None,progress=None):
            raise ValueError("bad")
        with self.assertRaises(ValueError):
            run_one_supervised_coverage_cycle(".",CoverageLoadBudget(),cycle_fn=cycle,sleep_fn=lambda s:None)
if __name__=="__main__":
    print("="*80);print(" OPC-024 CONCURRENCY RESILIENCE CORRECTION V2 CERTIFICATION TEST");print("="*80)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] PostgreSQL routing conflicts retry inside coverage child")
    print("[PASS] Retry exhaustion does not force child exit")
    print("[PASS] Programming errors remain fatal")
    print("[DONE] OPC-024 CONCURRENCY RESILIENCE CORRECTION V2 CERTIFIED")
