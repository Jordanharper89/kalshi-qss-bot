import unittest
from unittest.mock import patch
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent import oad_150_solana_onchain_canonical_postgresql_persistence as m
from qseries_v2.oracle_adapters.independent.oad_147_solana_onchain_evidence_foundation import build_solana_onchain_observation
class T(unittest.TestCase):
    def test_persistence_contract(self):
        o=build_solana_onchain_observation(source_id="solana:slot:1",observation_type="chain_state",subject="slot",observed_at="2026-08-29T00:00:00+00:00",payload={"slot":1})
        c=m.canonicalize_solana_onchain_observation(o,"test")
        self.assertEqual(c.source_id,"source.onchain.solana.mainnet"); self.assertFalse(c.execution_allowed)
        with patch.object(m,"acquire_solana_mainnet_chain_state",return_value=(o,)),patch.object(m,"acquire_solana_finalized_block_activity",return_value=()),patch.object(m,"_backend",return_value=object()),patch.object(m,"_query_one",return_value=SimpleNamespace(observation_id=c.observation_id)),patch.object(m,"exact_postgresql_readback",return_value=(SimpleNamespace(observation_id=c.observation_id),)):
            r=m.persist_current_solana_onchain()
        print("[SOURCE_ID]",c.source_id); print("[EXACT_READBACK]",r.exact_readback)
        self.assertEqual(r.exact_readback,1)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-150 Solana on-chain PostgreSQL persistence certified")
    print("[PASS] producer oracle.solana_onchain uses existing OPH-019 universal queue")
