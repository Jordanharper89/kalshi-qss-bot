import unittest
from qseries_v2.oracle_adapters.independent.oad_147_solana_onchain_evidence_foundation import build_solana_onchain_observation,validate_solana_onchain_observation
class T(unittest.TestCase):
    def test_foundation(self):
        o=build_solana_onchain_observation(source_id="solana:slot:1",observation_type="chain_state",subject="mainnet slot",observed_at="2026-08-29T00:00:00+00:00",payload={"slot":1})
        self.assertTrue(validate_solana_onchain_observation(o)); self.assertTrue(o.independent_evidence); self.assertFalse(o.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-147 Solana on-chain evidence foundation certified")
