import unittest
from qseries_v2.oracle_adapters.independent.oad_127_authoritative_economic_source_foundation import build_economic_observation,validate_economic_observation
class T(unittest.TestCase):
    def test_foundation(self):
        o=build_economic_observation(source_id="bls:test",provider="api.bls.gov",economic_family="inflation",observation_type="official_economic_release",subject="CPI",observed_at="2026-08-29T00:00:00+00:00",source_url="https://api.bls.gov/test",payload={"value":"1"})
        self.assertTrue(validate_economic_observation(o)); self.assertFalse(o.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-127 authoritative economic source foundation certified")
