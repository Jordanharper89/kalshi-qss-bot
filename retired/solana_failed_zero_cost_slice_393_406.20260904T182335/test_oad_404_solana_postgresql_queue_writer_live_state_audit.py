import unittest
from qseries_v2.oracle_adapters.independent.oad_404_solana_postgresql_queue_writer_live_state_audit import (
    audit_live_queue_writer_state,
    print_audit,
)

class T(unittest.TestCase):
    def test_live_postgresql_queue_writer_state(self):
        a=audit_live_queue_writer_state()
        print_audit(a)

        self.assertIsNotNone(a.queue_counts_raw)
        self.assertIn(
            a.diagnosis,
            {
                "STALE_WRITER_LEASE_OR_DEAD_OWNER",
                "WRITER_ALIVE_WITH_PENDING_QUEUE",
                "WRITER_ALIVE",
                "NO_WRITER_LEASE_WITH_PENDING_QUEUE",
                "NO_ACTIVE_WRITER_LEASE_OBSERVED",
                "WRITER_STATE_UNRESOLVED",
            },
        )
        self.assertFalse(a.execution_authority)

if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not rr.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-404 live PostgreSQL queue/writer state audit certified")
