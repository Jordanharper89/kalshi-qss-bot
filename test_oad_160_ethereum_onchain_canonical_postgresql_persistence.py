import unittest
from unittest.mock import patch
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent import oad_160_ethereum_onchain_canonical_postgresql_persistence as m
from qseries_v2.oracle_adapters.independent.oad_157_ethereum_onchain_evidence_foundation import build_ethereum_onchain_observation
class T(unittest.TestCase):
    def test_persistence(self):
        o=build_ethereum_onchain_observation(source_id="e:test",provider="ethereum-rpc.publicnode.com",source_url="https://ethereum-rpc.publicnode.com",observation_type="chain",subject="eth",observed_at="2026-08-29T00:00:00+00:00",payload={"x":1})
        c=m.canonicalize_ethereum_onchain_observation(o,"test")
        with patch.object(m,"acquire_ethereum_finalized_chain_observations",return_value=(o,)),patch.object(m,"acquire_ethereum_fee_transaction_pressure_observations",return_value=()),patch.object(m,"_backend",return_value=object()),patch.object(m,"_query_one",return_value=SimpleNamespace(observation_id=c.observation_id)),patch.object(m,"exact_postgresql_readback",return_value=(SimpleNamespace(observation_id=c.observation_id),)):
            r=m.persist_current_ethereum_onchain()
        print("[SOURCE_ID]",c.source_id); print("[PROVIDERS]",r.providers); print("[EXACT_READBACK]",r.exact_readback)
        self.assertEqual(r.exact_readback,1)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-160 resilient Ethereum persistence certified")
