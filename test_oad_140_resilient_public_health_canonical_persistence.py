import unittest
from unittest.mock import patch
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent import oad_140_resilient_public_health_canonical_persistence as m
from qseries_v2.oracle_adapters.independent.oad_137_authoritative_public_health_source_foundation import build_public_health_observation
class T(unittest.TestCase):
    def test_one_provider_can_fail(self):
        o=build_public_health_observation(source_id="cdc:test",provider="tools.cdc.gov",health_family="public_health",observation_type="official_health_publication",subject="CDC update",observed_at="2026-08-29T00:00:00+00:00",source_url="https://tools.cdc.gov/api/test",payload={"id":1})
        c=m.canonicalize_independent_observation(o,"test")
        with patch.object(m,"acquire_cdc_public_health_observations",return_value=(o,)), \
             patch.object(m,"acquire_openfda_enforcement_observations",side_effect=RuntimeError("provider down")), \
             patch.object(m,"_backend",return_value=object()), \
             patch.object(m,"_query_one",return_value=SimpleNamespace(observation_id=c.observation_id)), \
             patch.object(m,"exact_postgresql_readback",return_value=(SimpleNamespace(observation_id=c.observation_id),)):
            r=m.persist_resilient_public_health()
        print("[PROVIDER_STATES]",[(x.provider,x.state) for x in r.provider_results])
        print("[EXACT_READBACK]",r.exact_readback)
        self.assertEqual(r.exact_readback,1); self.assertEqual(r.provider_results[1].state,"UNAVAILABLE")
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-140 resilient public-health persistence certified")
