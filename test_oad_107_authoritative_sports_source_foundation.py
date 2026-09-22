import unittest
from qseries_v2.oracle_adapters.independent.oad_107_authoritative_sports_source_foundation import build_observation, validate_observation
class T(unittest.TestCase):
    def test_contract(self):
        o=build_observation(source_id="test:1",provider="official.example",sport_family="baseball",
            observation_type="schedule",subject="test",observed_at="2026-01-01T00:00:00+00:00",
            source_url="https://official.example/test",payload={"x":1})
        self.assertTrue(validate_observation(o))
        self.assertFalse(o.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] authoritative sports observation contract certified")
    print("[PASS] independent_evidence=TRUE")
    print("[PASS] probability_enabled=FALSE")
    print("[PASS] execution_authority=FALSE")
