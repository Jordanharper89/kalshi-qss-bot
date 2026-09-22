import unittest
from qseries_v2.oracle_intelligence_state.ois_048_service_health_aggregation import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_048_runtime_service_registry_health_aggregation())

    def test_degraded_required(self):
        x=aggregate_runtime_health((
            build_runtime_service_health("a",True,True,0),
            build_runtime_service_health("b",True,False,0),
        ))
        self.assertEqual(x.status,"DEGRADED")

    def test_lag_degrades(self):
        x=aggregate_runtime_health((build_runtime_service_health("a",True,True,31),))
        self.assertEqual(x.status,"DEGRADED")

if __name__=="__main__":
    print("="*72);print(" OIS-048 CERTIFICATION TEST");print(" RUNTIME SERVICE REGISTRY + HEALTH AGGREGATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Oracle runtime service health aggregation certified")
    print("[DONE] OIS-048 CERTIFIED")
