import unittest
from qseries_v2.oracle_adapters.independent.oad_252_crypto_independent_source_expansion_foundation import (
    build_independent_crypto_observation,
    verify_independent_crypto_observation,
)

class T(unittest.TestCase):
    def test_contract(self):
        x=build_independent_crypto_observation(
            source_id="source:test",
            provider="provider",
            source_class="exchange_liquidity",
            subject="BTC-USD",
            observation_type="orderbook",
            payload={"best_bid":100,"best_ask":101},
            observed_at="2026-09-01T00:00:00+00:00",
        )
        print("[SOURCE]",x.source_id)
        print("[CLASS]",x.source_class)
        print("[PROVENANCE]",x.provenance_hash)
        self.assertTrue(verify_independent_crypto_observation(x))
        self.assertTrue(x.independent_evidence)
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-252 independent-source provenance contract certified")
