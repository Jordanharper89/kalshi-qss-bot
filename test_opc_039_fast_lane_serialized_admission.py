import unittest
from qseries_v2.oracle_pre_settlement_coverage.opc_039_fast_lane_serialized_admission import verify_opc_039_fast_lane_serialized_admission

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_opc_039_fast_lane_serialized_admission())

if __name__=="__main__":
    print("="*80)
    print(" OPC-039 CERTIFICATION TEST")
    print(" FAST LANE SERIALIZED ADMISSION")
    print("="*80)

    result=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OPC-039 certified")
    print("[DONE] OPC-039 CERTIFIED")
