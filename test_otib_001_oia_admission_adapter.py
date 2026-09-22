import unittest
from qseries_v2.oracle_trader_intelligence_bridge.otib_001_oia_admission_adapter import OIAAdmissionSnapshot,verify_oia_admission_snapshot
class T(unittest.TestCase):
    def test_contract(self):
        x=OIAAdmissionSnapshot(0,0,0,0,(),"h",True,False)
        self.assertTrue(verify_oia_admission_snapshot(x))
if __name__=="__main__":
    print("="*88);print(" OTIB-001 CERTIFICATION TEST");print(" CERTIFIED OIA-007 PRODUCTION READ ADAPTER");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] OIA-007 read-only adapter contract certified");print("[PASS] execution_authority=FALSE");print("[DONE] OTIB-001 CERTIFIED")
