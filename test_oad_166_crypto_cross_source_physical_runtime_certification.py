import unittest
from qseries_v2.oracle_adapters.independent.oad_166_crypto_cross_source_physical_runtime_certification import run_crypto_cross_source_physical_runtime_certification

class T(unittest.TestCase):
    def test_physical(self):
        r=run_crypto_cross_source_physical_runtime_certification()
        print("[PHYSICAL] state=",r.state)
        print("[PHYSICAL] available_sources=",r.available_sources)
        print("[PHYSICAL] unavailable_sources=",r.unavailable_sources)
        print("[PHYSICAL] total_observations=",r.total_observations)
        print("[PHYSICAL] aligned_assets=",r.aligned_assets)
        print("[PHYSICAL] ready_for_evidence_comparison_assets=",r.ready_for_evidence_comparison_assets)
        print("[PHYSICAL] ready_assets=",r.ready_assets)
        print("[PHYSICAL] asset_states=",r.asset_states)
        print("[PHYSICAL] runtime_ready=",r.runtime_ready)
        self.assertTrue(r.runtime_ready)
        self.assertGreaterEqual(r.ready_for_evidence_comparison_assets,1)
        self.assertFalse(r.probability_enabled)
        self.assertFalse(r.direction_enabled)
        self.assertFalse(r.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-166 crypto cross-source physical runtime certified")
    print("[PASS] comparison readiness does not enable prediction, direction, or execution")
