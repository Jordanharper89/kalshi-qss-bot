import unittest
from qseries_v2.oracle_production_hardening.oph_010_physical_single_writer_production_gate import (
    verify_oph_010_physical_single_writer_production_gate,
)

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(
            verify_oph_010_physical_single_writer_production_gate()
        )

if __name__=="__main__":
    print("="*80)
    print(" OPH-010 CERTIFICATION TEST")
    print(" PHYSICAL SINGLE WRITER PRODUCTION GATE — CORRECTION V2")
    print("="*80)

    result=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OPH-006 through OPH-010 single-writer migration certified")
    print("[DONE] OPH-010 CERTIFIED")
