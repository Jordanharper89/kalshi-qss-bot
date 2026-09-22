import unittest
from qseries_v2.oracle_intelligence_state.ois_046_runtime_state import build_oracle_live_runtime_state
from qseries_v2.oracle_intelligence_state.ois_048_service_health_aggregation import build_runtime_service_health,aggregate_runtime_health
from qseries_v2.oracle_intelligence_state.ois_049_runtime_status_read_model import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_049_oracle_runtime_status_read_model())

    def test_read_only(self):
        r=build_oracle_live_runtime_state("RUNNING",1,True,True)
        h=aggregate_runtime_health((build_runtime_service_health("ois",True,True,0),))
        self.assertTrue(build_runtime_status_read_model(r,h,0,1).read_only)

    def test_negative_counter(self):
        r=build_oracle_live_runtime_state("RUNNING",1,True,True)
        h=aggregate_runtime_health((build_runtime_service_health("ois",True,True,0),))
        with self.assertRaises(ValueError):
            build_runtime_status_read_model(r,h,-1,1)

if __name__=="__main__":
    print("="*72);print(" OIS-049 CERTIFICATION TEST");print(" ORACLE RUNTIME STATUS READ MODEL");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Read-only Oracle runtime status model certified")
    print("[DONE] OIS-049 CERTIFIED")
