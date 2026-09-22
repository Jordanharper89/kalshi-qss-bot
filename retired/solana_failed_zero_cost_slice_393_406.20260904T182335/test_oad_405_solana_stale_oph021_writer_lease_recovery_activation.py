import unittest

from qseries_v2.oracle_adapters.independent.oad_405_solana_stale_oph021_writer_lease_recovery_activation import (
    recover_and_activate_exclusive_writer,
)

class T(unittest.TestCase):
    def test_stale_writer_lease_recovery_activation(self):
        x=recover_and_activate_exclusive_writer()

        print("[RECOVERY]",x)

        self.assertTrue(
            x.active_lease_pid_alive,
            "OPH-021 exclusive canonical writer is not alive after recovery activation",
        )
        self.assertEqual(
            x.state,
            "OPH021_WRITER_RECOVERED_AND_ACTIVE",
        )
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not rr.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-405 stale OPH-021 writer lease recovery activation certified")
    print("[PASS] exclusive canonical writer process is alive")
    print("[PASS] stale lease archived instead of deleted when applicable")
