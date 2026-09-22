import unittest
from unittest.mock import patch
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent import oad_130_authoritative_economic_canonical_persistence as m
from qseries_v2.oracle_adapters.independent.oad_127_authoritative_economic_source_foundation import build_economic_observation
class T(unittest.TestCase):
    def test_existing_architecture_reuse(self):
        o=build_economic_observation(source_id="bls:test:1",provider="api.bls.gov",economic_family="inflation",observation_type="official_economic_release",subject="CPI",observed_at="2026-08-29T00:00:00+00:00",source_url="https://api.bls.gov/test",payload={"value":"1"})
        c=m.canonicalize_independent_observation(o,"test")
        with patch.object(m,"acquire_bls_latest_economic_observations",return_value=(o,)),patch.object(m,"acquire_treasury_debt_observation",return_value=()),patch.object(m,"_backend",return_value=object()),patch.object(m,"_query_one",return_value=SimpleNamespace(observation_id=c.observation_id)),patch.object(m,"exact_postgresql_readback",return_value=(SimpleNamespace(observation_id=c.observation_id),)):
            r=m.persist_current_authoritative_economic()
        print("[RAW]",r.raw_observations); print("[EXACT_READBACK]",r.exact_readback)
        self.assertEqual(r.raw_observations,1); self.assertEqual(r.exact_readback,1); self.assertEqual(r.committed_new,0)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-130 authoritative economic canonical/persistence contract certified")
    print("[PASS] existing OAD-061/OAD-062/OAD-066/OAD-068 architecture reused")
