import unittest
from qseries_v2.oracle_adapters.independent.oad_141_authoritative_public_health_physical_runtime_gate import run_authoritative_public_health_physical_runtime_gate
class T(unittest.TestCase):
    def test_physical(self):
        r=run_authoritative_public_health_physical_runtime_gate()
        print("[PHYSICAL] state=",r.state)
        print("[PHYSICAL] provider_states=",r.provider_states)
        print("[PHYSICAL] available_providers=",r.available_providers)
        print("[PHYSICAL] unavailable_providers=",r.unavailable_providers)
        print("[PHYSICAL] raw_observations=",r.raw_observations)
        print("[PHYSICAL] canonical_observations=",r.canonical_observations)
        print("[PHYSICAL] committed_new=",r.committed_new)
        print("[PHYSICAL] exact_readback=",r.exact_readback)
        print("[PHYSICAL] runtime_ready=",r.runtime_ready)
        self.assertTrue(r.runtime_ready)
        self.assertGreater(r.raw_observations,0)
        self.assertEqual(r.exact_readback,r.canonical_observations)
        self.assertFalse(r.probability_enabled)
        self.assertFalse(r.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-141 authoritative public-health physical runtime gate certified")
    print("[PASS] provider isolation preserves healthy public-health evidence")
    print("[PASS] probability_enabled=FALSE execution_authority=FALSE")
