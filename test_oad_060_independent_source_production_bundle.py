import unittest
from qseries_v2.oracle_adapters.independent.oad_060_independent_source_bundle import *

class T(unittest.TestCase):
    def test_physical_bundle(self):
        r=acquire_independent_production_bundle(2)
        print("[PHYSICAL] provider_counts="+str(r.provider_counts))
        print("[PHYSICAL] independent_observations="+str(len(r.observations)))
        self.assertEqual(
            r.providers,
            ("weather.gov","federalregister.gov","usgs.gov"),
        )
        self.assertGreater(len(r.observations),0)
        self.assertTrue(r.read_only)
        self.assertFalse(r.execution_authority)
        self.assertTrue(all(
            x.source_class=="authoritative_real_world"
            for x in r.observations
        ))

if __name__=="__main__":
    print("="*72)
    print(" OAD-060 PHYSICAL CERTIFICATION TEST")
    print(" INDEPENDENT SOURCE PRODUCTION BUNDLE")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Multiple authoritative non-Kalshi sources physically acquired")
    print("[PASS] Independent evidence remains read-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OAD-060 CERTIFIED")
