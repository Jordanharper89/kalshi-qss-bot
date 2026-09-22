import unittest
from qseries_v2.oracle_adapters.independent.oad_146_coinbase_crypto_physical_runtime_readiness_gate import run_coinbase_crypto_physical_runtime_readiness_gate
class T(unittest.TestCase):
    def test_physical(self):
        r=run_coinbase_crypto_physical_runtime_readiness_gate()
        print("[PHYSICAL] state=",r.state)
        print("[PHYSICAL] discovered_products=",r.discovered_products)
        print("[PHYSICAL] acquired_observations=",r.acquired_observations)
        print("[PHYSICAL] canonical_observations=",r.canonical_observations)
        print("[PHYSICAL] committed_new=",r.committed_new)
        print("[PHYSICAL] exact_readback=",r.exact_readback)
        print("[PHYSICAL] market_native_reference=",r.market_native_reference)
        print("[PHYSICAL] independent_evidence=",r.independent_evidence)
        print("[PHYSICAL] runtime_ready=",r.runtime_ready)
        self.assertTrue(r.runtime_ready); self.assertTrue(r.market_native_reference)
        self.assertFalse(r.independent_evidence); self.assertFalse(r.probability_enabled); self.assertFalse(r.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-146 Coinbase crypto physical runtime readiness certified")
    print("[PASS] Coinbase remains market-native reference, not independent evidence")
