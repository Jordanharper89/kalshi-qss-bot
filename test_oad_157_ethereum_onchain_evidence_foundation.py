import unittest
from qseries_v2.oracle_adapters.independent.oad_157_ethereum_onchain_evidence_foundation import build_ethereum_onchain_observation,validate_ethereum_onchain_observation
class T(unittest.TestCase):
    def test_both_providers(self):
        for provider,url in (("cloudflare-eth.com","https://cloudflare-eth.com/v1/mainnet"),("ethereum-rpc.publicnode.com","https://ethereum-rpc.publicnode.com")):
            o=build_ethereum_onchain_observation(source_id="e:1",provider=provider,source_url=url,observation_type="chain",subject="eth",observed_at="2026-08-29T00:00:00+00:00",payload={"x":1})
            self.assertTrue(validate_ethereum_onchain_observation(o))
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-157 resilient Ethereum provider foundation certified")
