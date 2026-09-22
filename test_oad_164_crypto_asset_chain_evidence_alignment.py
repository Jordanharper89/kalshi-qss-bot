import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_164_crypto_asset_chain_evidence_alignment import align_crypto_asset_chain_evidence

class T(unittest.TestCase):
    def test_payload_identity_alignment(self):
        obs=(
            ("coinbase",SimpleNamespace(subject="BTC-USD",payload={"base_currency":"BTC"},observed_at="2026-08-29T00:10:00+00:00")),
            ("bitcoin",SimpleNamespace(subject="Bitcoin chain",payload={},observed_at="2026-08-29T00:00:00+00:00")),
        )
        r=align_crypto_asset_chain_evidence(SimpleNamespace(observations=obs))
        btc=r[0]
        print("[BTC_MARKET]",btc.market_source_present)
        print("[BTC_CHAIN]",btc.chain_source_present)
        print("[BTC_SPAN]",btc.observation_time_span_seconds)
        self.assertTrue(btc.evidence_comparison_possible)
        self.assertEqual(btc.observation_time_span_seconds,600.0)
        self.assertIsNone(btc.direction); self.assertIsNone(btc.probability)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-164 exact asset/chain alignment certified")
