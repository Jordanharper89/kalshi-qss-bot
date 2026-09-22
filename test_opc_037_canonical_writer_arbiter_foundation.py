import unittest
from qseries_v2.oracle_pre_settlement_coverage.opc_037_canonical_writer_arbiter_foundation import verify_opc_037_canonical_writer_arbiter_foundation

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_opc_037_canonical_writer_arbiter_foundation())

if __name__=="__main__":
    print("="*80)
    print(" OPC-037 CERTIFICATION TEST")
    print(" CANONICAL WRITER ARBITER FOUNDATION")
    print("="*80)

    result=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OPC-037 certified")
    print("[DONE] OPC-037 CERTIFIED")
