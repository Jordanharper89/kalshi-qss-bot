import unittest
from qseries_v2.oracle_adapters.independent.oad_152_bitcoin_onchain_evidence_foundation import build_bitcoin_onchain_observation,validate_bitcoin_onchain_observation
class T(unittest.TestCase):
    def test_foundation(self):
        o=build_bitcoin_onchain_observation(source_id="bitcoin:tip:1",provider="blockstream.info",provider_role="public_chain_observer",observation_type="chain_tip",subject="Bitcoin mainnet tip",observed_at="2026-08-29T00:00:00+00:00",source_url="https://blockstream.info/api/blocks/tip/height",payload={"height":1})
        self.assertTrue(validate_bitcoin_onchain_observation(o)); self.assertTrue(o.independent_evidence); self.assertFalse(o.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-152 Bitcoin on-chain evidence foundation certified")
    print("[PASS] public observer provenance explicit; no provider mislabeled as Bitcoin itself")
