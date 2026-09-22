import unittest
from qseries_v2.oracle_intelligence_state.ois_054_operator_status_boundary import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_054_oracle_runtime_operator_status_boundary())

    def test_read_only(self):
        from qseries_v2.oracle_intelligence_state.ois_046_runtime_state import build_oracle_live_runtime_state
        from qseries_v2.oracle_intelligence_state.ois_048_service_health_aggregation import build_runtime_service_health,aggregate_runtime_health
        from qseries_v2.oracle_intelligence_state.ois_049_runtime_status_read_model import build_runtime_status_read_model
        r=build_oracle_live_runtime_state("RUNNING",1,True,True)
        h=aggregate_runtime_health((build_runtime_service_health("ois",True,True,0),))
        self.assertTrue(project_operator_runtime_status(build_runtime_status_read_model(r,h,0,1)).read_only)

if __name__=="__main__":
    print("="*72);print(" OIS-054 CERTIFICATION TEST");print(" ORACLE RUNTIME OPERATOR STATUS BOUNDARY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Read-only Operator Terminal/API runtime status boundary certified")
    print("[DONE] OIS-054 CERTIFIED")
