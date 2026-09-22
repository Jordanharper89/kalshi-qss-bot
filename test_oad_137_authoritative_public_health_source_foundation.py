import unittest
from qseries_v2.oracle_adapters.independent.oad_137_authoritative_public_health_source_foundation import build_public_health_observation,validate_public_health_observation
class T(unittest.TestCase):
    def test_foundation(self):
        o=build_public_health_observation(source_id="cdc:test",provider="tools.cdc.gov",health_family="public_health",observation_type="official_health_publication",subject="CDC update",observed_at="2026-08-29T00:00:00+00:00",source_url="https://tools.cdc.gov/api/test",payload={"id":1})
        self.assertTrue(validate_public_health_observation(o)); self.assertFalse(o.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-137 authoritative public-health source foundation certified")
