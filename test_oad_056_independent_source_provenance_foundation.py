import unittest
from qseries_v2.oracle_adapters.independent.oad_056_independent_source_provenance import *
class T(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_oad_056_independent_source_provenance_foundation())
    def test_kalshi_rejected(self):
        with self.assertRaises(ValueError):
            build_independent_observation(source_id="kalshi",source_class="prediction_market",observation_type="price",
                subject="x",observed_at="x",source_url="https://kalshi.com",payload={})
    def test_execution_false(self):
        x=build_independent_observation(source_id="gov",source_class="authoritative_real_world",observation_type="event",
            subject="x",observed_at="x",source_url="https://example.gov",payload={})
        self.assertFalse(x.execution_authority)
if __name__=="__main__":
    print("="*72); print(" OAD-056 CERTIFICATION TEST"); print(" INDEPENDENT SOURCE PROVENANCE FOUNDATION"); print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi-derived evidence rejected as independent")
    print("[PASS] Independent provenance contract certified")
    print("[DONE] OAD-056 CERTIFIED")
