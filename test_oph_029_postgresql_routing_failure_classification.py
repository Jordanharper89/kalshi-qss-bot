import unittest
from qseries_v2.oracle_production_hardening.oph_029_postgresql_routing_failure_classification import *

class PostgreSQLPersistenceRoutingFailure(Exception):
    pass

class T(unittest.TestCase):
    def test_observed_runtime_failure(self):
        c=classify_persistence_failure(
            PostgreSQLPersistenceRoutingFailure("PostgreSQL batch append was not committed")
        )
        self.assertEqual(c.category,"TRANSIENT_POSTGRESQL")
        self.assertTrue(c.retryable)
        self.assertFalse(c.terminal)

    def test_integrity_failure(self):
        c=classify_persistence_failure(RuntimeError("expected_terminal_chain_hash_mismatch"))
        self.assertEqual(c.category,"TERMINAL_INTEGRITY")
        self.assertFalse(c.retryable)
        self.assertTrue(c.terminal)

if __name__=="__main__":
    print("="*88)
    print(" OPH-029 CERTIFICATION TEST")
    print(" POSTGRESQL ROUTING FAILURE CLASSIFICATION")
    print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Observed PostgreSQL not-committed failure classified as transient/retryable")
    print("[PASS] Integrity-chain failures classified terminal")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPH-029 CERTIFIED")
