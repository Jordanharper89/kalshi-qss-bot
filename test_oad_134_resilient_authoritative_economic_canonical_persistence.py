import unittest
from unittest.mock import patch
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent import oad_134_resilient_authoritative_economic_canonical_persistence as m
from qseries_v2.oracle_adapters.independent.oad_127_authoritative_economic_source_foundation import build_economic_observation
class T(unittest.TestCase):
    def test_healthy_provider_persists_when_other_provider_failed(self):
        o=build_economic_observation(source_id="bls:test",provider="api.bls.gov",economic_family="inflation",observation_type="official_economic_release",subject="CPI",observed_at="2026-08-29T00:00:00+00:00",source_url="https://api.bls.gov/test",payload={"value":"1"})
        c=m.canonicalize_independent_observation(o,"test")
        provider=(SimpleNamespace(provider="api.bls.gov",state="AVAILABLE",observation_count=1,error_type=None,error_message=None,checked_at="t1"),SimpleNamespace(provider="api.fiscaldata.treasury.gov",state="UNAVAILABLE",observation_count=0,error_type="URLError",error_message="tls",checked_at="t2"))
        with patch.object(m,"acquire_resilient_authoritative_economic",return_value=(provider,(o,))), \
             patch.object(m,"_backend",return_value=object()), \
             patch.object(m,"_query_one",return_value=SimpleNamespace(observation_id=c.observation_id)), \
             patch.object(m,"exact_postgresql_readback",return_value=(SimpleNamespace(observation_id=c.observation_id),)):
            r=m.persist_resilient_authoritative_economic()
        print("[RAW]",r.raw_observations); print("[EXACT_READBACK]",r.exact_readback); print("[SOURCE_HEALTH]",[(x.provider,x.state) for x in r.source_health])
        self.assertEqual(r.raw_observations,1); self.assertEqual(r.exact_readback,1); self.assertEqual(len(r.source_health),2)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-134 resilient economic persistence certified")
