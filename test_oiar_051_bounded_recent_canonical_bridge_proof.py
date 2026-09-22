import unittest
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_051_bounded_recent_canonical_bridge_proof import (
    prove_bounded_recent_canonical_bridge,
    verify_oiar_051_bounded_recent_canonical_bridge_proof,
)

class T(unittest.TestCase):
    def test_physical_bridge(self):
        x=prove_bounded_recent_canonical_bridge()
        self.assertGreater(x.recent_rows_scanned,0)
        self.assertGreater(x.active_opc_candidates,0)
        self.assertGreater(x.checked,0)
        self.assertGreater(x.matched_market_snapshots,0)
        self.assertGreater(x.exact_ticker_matches,0)
        self.assertEqual(x.exact_ticker_matches,x.matched_market_snapshots)
        self.assertTrue(x.exact_lookup_uses_index)
        self.assertTrue(x.read_only)
        self.assertFalse(x.execution_authority)

    def test_verifier(self):
        self.assertTrue(verify_oiar_051_bounded_recent_canonical_bridge_proof())

if __name__=="__main__":
    print("="*88)
    print(" OIAR-051 CERTIFICATION TEST")
    print(" BOUNDED RECENT CANONICAL BRIDGE PROOF")
    print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] bounded recent ACTIVE OPC candidates physically proven")
    print("[PASS] exact OIAR-003 indexed identity matches physically proven")
    print("[PASS] read_only=TRUE")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-051 CERTIFIED")
