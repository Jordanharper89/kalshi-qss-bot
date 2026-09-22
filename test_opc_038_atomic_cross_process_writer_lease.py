import unittest
from qseries_v2.oracle_pre_settlement_coverage.opc_038_atomic_cross_process_writer_lease import verify_opc_038_atomic_cross_process_writer_lease

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_opc_038_atomic_cross_process_writer_lease())

if __name__=="__main__":
    print("="*80)
    print(" OPC-038 CERTIFICATION TEST")
    print(" ATOMIC CROSS PROCESS WRITER LEASE")
    print("="*80)

    result=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OPC-038 certified")
    print("[DONE] OPC-038 CERTIFIED")
