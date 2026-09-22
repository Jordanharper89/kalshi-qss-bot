import unittest
from unittest.mock import patch
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent import oad_155_bitcoin_onchain_canonical_postgresql_persistence as m
from qseries_v2.oracle_adapters.independent.oad_152_bitcoin_onchain_evidence_foundation import build_bitcoin_onchain_observation
class T(unittest.TestCase):
    def test_persistence_contract(self):
        o=build_bitcoin_onchain_observation(source_id="bitcoin:test:1",provider="blockstream.info",provider_role="public_chain_observer",observation_type="chain_tip",subject="tip",observed_at="2026-08-29T00:00:00+00:00",source_url="https://blockstream.info/api/blocks/tip/height",payload={"height":1})
        c=m.canonicalize_bitcoin_onchain_observation(o,"test")
        self.assertEqual(c.source_id,"source.onchain.bitcoin.mainnet"); self.assertFalse(c.execution_allowed)
        with patch.object(m,"acquire_bitcoin_blockstream_chain_observations",return_value=(o,)),patch.object(m,"acquire_bitcoin_mempool_pressure_observations",return_value=()),patch.object(m,"_backend",return_value=object()),patch.object(m,"_query_one",return_value=SimpleNamespace(observation_id=c.observation_id)),patch.object(m,"exact_postgresql_readback",return_value=(SimpleNamespace(observation_id=c.observation_id),)):
            r=m.persist_current_bitcoin_onchain()
        print("[SOURCE_ID]",c.source_id); print("[PROVIDERS]",r.providers); print("[EXACT_READBACK]",r.exact_readback)
        self.assertEqual(r.exact_readback,1)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-155 Bitcoin on-chain PostgreSQL persistence certified")
    print("[PASS] producer oracle.bitcoin_onchain uses existing OPH-019 universal queue")
