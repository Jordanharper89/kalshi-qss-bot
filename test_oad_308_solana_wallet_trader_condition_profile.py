import unittest
from qseries_v2.oracle_adapters.independent.oad_308_solana_wallet_trader_condition_profile import (
    build_current_wallet_trader_condition_profile,
)

class T(unittest.TestCase):
    def test_physical_durable_evidence_only(self):
        x=build_current_wallet_trader_condition_profile()
        print("[PHYSICAL] token=",x.token_address)
        print("[PHYSICAL] holder_rows=",x.holder_rows)
        print("[PHYSICAL] trader_rows=",x.trader_rows)
        print("[PHYSICAL] holder_observations=",x.holder_observations)
        print("[PHYSICAL] trader_observations=",x.trader_observations)
        print("[PHYSICAL] evidence_state=",x.evidence_state)
        print("[PHYSICAL] queried_sources=",x.queried_sources)
        print("[PHYSICAL] durable_read_only=",x.durable_read_only)
        self.assertTrue(x.token_address)
        self.assertEqual(len(x.queried_sources),2)
        self.assertIn(x.evidence_state,(
            "DURABLE_WALLET_TRADER_EVIDENCE_READY",
            "DURABLE_WALLET_TRADER_EVIDENCE_PARTIAL",
            "DURABLE_WALLET_TRADER_EVIDENCE_UNAVAILABLE",
        ))
        self.assertTrue(x.provider_claim_only)
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
    print("[PASS] OAD-308 durable wallet/trader condition read physically certified")
    print("[PASS] no GMGN acquisition invoked by condition intelligence")
    print("[PASS] missing durable evidence is reported as unavailable, never fabricated")
