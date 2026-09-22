import unittest
from qseries_v2.oracle_adapters.independent.oad_151_solana_onchain_physical_runtime_certification import run_solana_onchain_physical_runtime_certification
class T(unittest.TestCase):
    def test_physical(self):
        r=run_solana_onchain_physical_runtime_certification()
        print("[PHYSICAL] state=",r.state)
        print("[PHYSICAL] raw_observations=",r.raw_observations)
        print("[PHYSICAL] canonical_observations=",r.canonical_observations)
        print("[PHYSICAL] committed_new=",r.committed_new)
        print("[PHYSICAL] exact_readback=",r.exact_readback)
        print("[PHYSICAL] source_class=",r.source_class)
        print("[PHYSICAL] independent_evidence=",r.independent_evidence)
        print("[PHYSICAL] runtime_ready=",r.runtime_ready)
        self.assertTrue(r.runtime_ready); self.assertEqual(r.source_class,"underlying_chain_state")
        self.assertTrue(r.independent_evidence); self.assertFalse(r.probability_enabled); self.assertFalse(r.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-151 Solana on-chain physical runtime certified")
    print("[PASS] underlying chain state remains distinct from Coinbase market-native reference")
    print("[PASS] probability_enabled=FALSE execution_authority=FALSE")
