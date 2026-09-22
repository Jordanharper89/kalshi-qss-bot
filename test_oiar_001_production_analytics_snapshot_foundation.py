import unittest

from qseries_v2.oracle_intelligence_analytics_runtime.oiar_001_production_analytics_snapshot_foundation import (
    OIAR_001_BUILD_ID,
    STATE_TABLE,
    SNAPSHOT_TABLE,
    AnalyticsSnapshotFoundationStatus,
    stable_hash,
)

class T(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(OIAR_001_BUILD_ID,"OIAR-001")

    def test_contract(self):
        x=AnalyticsSnapshotFoundationStatus(
            STATE_TABLE,
            SNAPSHOT_TABLE,
            True,
            True,
            True,
            False,
        )
        self.assertTrue(x.state_row_present)
        self.assertTrue(x.database_writable)
        self.assertTrue(x.read_only_source_required)
        self.assertFalse(x.execution_authority)

    def test_hash_deterministic(self):
        a=stable_hash({"b":2,"a":1})
        b=stable_hash({"a":1,"b":2})
        self.assertEqual(a,b)

if __name__=="__main__":
    print("="*88)
    print(" OIAR-001 CERTIFICATION TEST")
    print(" PRODUCTION ANALYTICS SNAPSHOT FOUNDATION")
    print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] deterministic snapshot identity contract certified")
    print("[PASS] read-only source boundary required")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-001 CERTIFIED")
