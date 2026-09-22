import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_135_authoritative_economic_partial_coverage_certification import certify_economic_partial_coverage
class T(unittest.TestCase):
    def test_partial_is_usable(self):
        p=SimpleNamespace(
            provider_results=(
                SimpleNamespace(provider="api.bls.gov",state="AVAILABLE"),
                SimpleNamespace(provider="api.fiscaldata.treasury.gov",state="UNAVAILABLE"),
            ),
            raw_observations=3,canonical_observations=3,exact_readback=3,
        )
        r=certify_economic_partial_coverage(p)
        print("[STATE]",r.state); print("[AVAILABLE]",r.available_providers); print("[UNAVAILABLE]",r.unavailable_providers)
        self.assertEqual(r.state,"PARTIAL_COVERAGE")
        self.assertTrue(r.coverage_usable)
        self.assertFalse(r.full_provider_coverage)
        self.assertFalse(r.probability_enabled)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-135 partial economic coverage certification certified")
