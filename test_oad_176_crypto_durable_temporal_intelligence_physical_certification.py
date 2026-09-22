import unittest
from qseries_v2.oracle_adapters.independent.oad_176_crypto_durable_temporal_intelligence_physical_certification import (
    run_crypto_durable_temporal_intelligence_physical_certification,
)
class T(unittest.TestCase):
    def test_physical(self):
        r=run_crypto_durable_temporal_intelligence_physical_certification()
        print("[PHYSICAL] seed_runtime_ready=",r.seed_runtime_ready)
        print("[PHYSICAL] comparison_runtime_ready=",r.comparison_runtime_ready)
        print("[PHYSICAL] historical_states=",r.historical_states)
        print("[PHYSICAL] exact_prior_states=",r.exact_prior_states)
        print("[PHYSICAL] comparable_temporal_metrics=",r.comparable_temporal_metrics)
        print("[PHYSICAL] increased=",r.increased)
        print("[PHYSICAL] decreased=",r.decreased)
        print("[PHYSICAL] unchanged=",r.unchanged)
        print("[PHYSICAL] no_comparable_history=",r.no_comparable_history)
        print("[PHYSICAL] cross_source_assets=",r.cross_source_assets)
        print("[PHYSICAL] exact_readback=",r.exact_readback)
        print("[PHYSICAL] physical_ready=",r.physical_ready)
        self.assertTrue(r.physical_ready)
        self.assertGreater(r.comparable_temporal_metrics,0)
        self.assertGreater(r.exact_prior_states,0)
        self.assertFalse(r.probability_enabled)
        self.assertFalse(r.direction_enabled)
        self.assertFalse(r.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-176 durable crypto temporal intelligence physically certified")
    print("[PASS] prior-state comparison is PostgreSQL-backed; prediction/direction/probability/execution remain disabled")
