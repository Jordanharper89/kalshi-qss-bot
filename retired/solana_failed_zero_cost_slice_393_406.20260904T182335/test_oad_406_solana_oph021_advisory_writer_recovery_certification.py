import unittest
from qseries_v2.oracle_adapters.independent.oad_406_solana_oph021_advisory_writer_recovery_certification import (
    certify_oph021_advisory_writer,
)

class T(unittest.TestCase):
    def test_physical_advisory_writer_boundary(self):
        x=certify_oph021_advisory_writer()
        print("[OAD-406]",x)
        if x.output_excerpt:
            print("[WRITER OUTPUT]")
            print(x.output_excerpt)

        self.assertIn(
            x.state,
            {
                "OPH021_ADVISORY_WRITER_ACTIVE_BY_PROBE",
                "OPH021_ADVISORY_WRITER_ALREADY_ACTIVE",
                "OPH021_ADVISORY_WRITER_ACQUIRED_AND_CLEAN",
            },
            "OPH-021 advisory-lock writer boundary was not physically certified",
        )

        if x.failed_before is not None and x.failed_after is not None:
            self.assertLessEqual(
                x.failed_after,
                x.failed_before,
                "OPH-021 certification caused FAILED queue growth",
            )

        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not rr.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-406 OPH-021 PostgreSQL advisory-writer recovery certification PASSED")
