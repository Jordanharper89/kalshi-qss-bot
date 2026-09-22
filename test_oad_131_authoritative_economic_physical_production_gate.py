import unittest
from qseries_v2.oracle_adapters.independent.oad_131_authoritative_economic_physical_production_gate import run_authoritative_economic_physical_production_gate
class T(unittest.TestCase):
    def test_physical_network_postgresql(self):
        r=run_authoritative_economic_physical_production_gate()
        print("[PHYSICAL] raw_observations=",r.raw_observations)
        print("[PHYSICAL] canonical_observations=",r.canonical_observations)
        print("[PHYSICAL] provenance_validated=",r.provenance_validated)
        print("[PHYSICAL] already_present=",r.already_present)
        print("[PHYSICAL] committed_new=",r.committed_new)
        print("[PHYSICAL] exact_readback=",r.exact_readback)
        print("[PHYSICAL] providers=",r.providers)
        print("[PHYSICAL] certified=",r.certified)
        self.assertTrue(r.certified); self.assertFalse(r.probability_enabled); self.assertFalse(r.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-131 physical authoritative economic production gate certified")
    print("[PASS] official BLS/Treasury -> canonical -> PostgreSQL single writer -> exact readback")
    print("[PASS] probability_enabled=FALSE execution_authority=FALSE")
