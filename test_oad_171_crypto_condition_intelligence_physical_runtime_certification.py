import unittest
from qseries_v2.oracle_adapters.independent.oad_171_crypto_condition_intelligence_physical_runtime_certification import run_crypto_condition_intelligence_physical_runtime_certification
class T(unittest.TestCase):
    def test_physical(self):
        r=run_crypto_condition_intelligence_physical_runtime_certification()
        print("[PHYSICAL] state=",r.state)
        print("[PHYSICAL] available_sources=",r.available_sources)
        print("[PHYSICAL] unavailable_sources=",r.unavailable_sources)
        print("[PHYSICAL] raw_observations=",r.raw_observations)
        print("[PHYSICAL] structured_metrics=",r.structured_metrics)
        print("[PHYSICAL] condition_states=",r.condition_states)
        print("[PHYSICAL] temporal_changes=",r.temporal_changes)
        print("[PHYSICAL] comparable_temporal_metrics=",r.comparable_temporal_metrics)
        print("[PHYSICAL] cross_source_assets=",r.cross_source_assets)
        print("[PHYSICAL] profiles=",tuple((x.asset,x.evidence_state,x.consistency_state,x.market_native_metrics,x.independent_chain_metrics) for x in r.profiles))
        print("[PHYSICAL] runtime_ready=",r.runtime_ready)
        self.assertTrue(r.runtime_ready)
        self.assertGreaterEqual(len(r.cross_source_assets),1)
        self.assertFalse(r.probability_enabled)
        self.assertFalse(r.direction_enabled)
        self.assertFalse(r.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-171 crypto condition intelligence physical runtime certified")
    print("[PASS] condition intelligence does not enable prediction, direction, probability, or execution")
