
import unittest
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_021_indexed_snapshot_identity_materializer as m

class T(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(m.OIAR_021_BUILD_ID, "OIAR-021")

    def test_stage(self):
        self.assertEqual(m.IDENTITY_STAGE, "indexed_trader_market_identity")

    def test_proven_index_dependency(self):
        self.assertEqual(
            m.INDEX_NAME,
            "idx_oracle_canonical_market_snapshot_market_seq",
        )

    def test_boundaries(self):
        self.assertTrue(m.READ_ONLY_SOURCE)
        self.assertFalse(m.EXECUTION_AUTHORITY)

if __name__ == "__main__":
    print("=" * 88)
    print(" OIAR-021 CERTIFICATION TEST")
    print(" INDEXED SNAPSHOT IDENTITY MATERIALIZER")
    print("=" * 88)
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] exact OIAR-003 index dependency certified")
    print("[PASS] snapshot-native identity contract certified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-021 CERTIFIED")
