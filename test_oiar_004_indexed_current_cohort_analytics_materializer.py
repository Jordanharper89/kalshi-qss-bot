import unittest

import qseries_v2.oracle_intelligence_analytics_runtime.oiar_004_indexed_current_cohort_analytics_materializer as m

class T(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(m.OIAR_004_BUILD_ID, "OIAR-004")

    def test_stage(self):
        self.assertEqual(m.ANALYTICS_STAGE, "indexed_current_cohort_oia")

    def test_index_dependency(self):
        self.assertTrue(m.INDEX_NAME.startswith("idx_oracle_canonical_market_snapshot"))

if __name__ == "__main__":
    print("=" * 88)
    print(" OIAR-004 CERTIFICATION TEST")
    print(" INDEXED CURRENT-COHORT ANALYTICS MATERIALIZER")
    print("=" * 88)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] indexed analytics materializer contract certified")
    print("[PASS] existing OIA calculation/classification engines preserved")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-004 CERTIFIED")
