import unittest
from qseries_v2.oracle_adapters.independent.oad_403_solana_oph019_021_ingestion_completion_audit import (
    audit_ingestion_completion,
    print_audit,
)

class T(unittest.TestCase):
    def test_exact_topology_and_runtime_audit(self):
        a=audit_ingestion_completion()
        print_audit(a)

        self.assertIn("submit_observation_batch", a.oph019_functions)
        self.assertIn("await_request", a.oph019_functions)
        self.assertTrue(
            a.oph021_functions or a.oph021_classes,
            "OPH-021 writer module exposed no callable/class topology"
        )
        self.assertIn(
            a.conclusion,
            {
                "TIMED_OUT_REQUEST_LATER_COMPLETED",
                "TIMED_OUT_REQUEST_FAILED",
                "TIMED_OUT_REQUEST_STILL_PENDING_OR_PROCESSING",
                "REQUEST_FOUND_STATUS_UNRESOLVED",
                "REQUEST_NOT_FOUND_IN_DURABLE_RUNTIME_STATE",
            },
        )

if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not rr.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-403 exact OPH-019/021 Solana ingestion completion audit certified")
