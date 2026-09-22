import unittest
from qseries_v2.oracle_production_hardening.oph_018_current_competing_writer_identification import (
    verify_oph_018_current_competing_writer_identification,
)

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(
            verify_oph_018_current_competing_writer_identification()
        )

if __name__ == "__main__":
    print("=" * 80)
    print(" OPH-018 CERTIFICATION TEST")
    print(" CURRENT COMPETING WRITER IDENTIFICATION")
    print("=" * 80)

    r = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OPH-018 certified")
    print("[DONE] OPH-018 CERTIFIED")
