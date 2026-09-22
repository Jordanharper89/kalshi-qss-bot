import unittest

from qseries_v2.oracle_adapters.independent.oad_307_solana_temporal_market_condition_profile import (
    DISCOVERY_SOURCE_ID,
    build_current_temporal_market_condition_profile,
)

class T(unittest.TestCase):
    def test_physical_durable_read_only(self):
        x=build_current_temporal_market_condition_profile()
        print("[PHYSICAL] token=",x.token_address)
        print("[PHYSICAL] queried_rows=",x.queried_rows)
        print("[PHYSICAL] queried_sources=",x.queried_sources)
        print("[PHYSICAL] pair_conditions=",len(x.pair_conditions))
        print("[PHYSICAL] ready_pairs=",x.ready_pairs)
        print("[PHYSICAL] evidence_state=",x.evidence_state)
        print("[PHYSICAL] durable_read_only=",x.durable_read_only)

        self.assertTrue(x.token_address)
        self.assertGreaterEqual(x.queried_rows,1)
        self.assertIn(DISCOVERY_SOURCE_ID,x.queried_sources)
        self.assertIn(
            "source.dex.solana.token_pools."+x.token_address,
            x.queried_sources,
        )
        self.assertIn(
            "source.onchain.solana.mint."+x.token_address,
            x.queried_sources,
        )
        self.assertTrue(x.durable_read_only)
        self.assertIsNone(x.probability)
        self.assertIsNone(x.direction)
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-307 exact durable PostgreSQL history read physically certified")
    print("[PASS] no refresh acquisition or production write required")
    print("[PASS] probability=FALSE direction=FALSE execution=FALSE")
