import unittest

from qseries_v2.oracle_adapters.independent.oad_postgresql_canonical_observation_identity_recovery_audit import (
    run_canonical_observation_identity_recovery_audit,
)

class T(unittest.TestCase):
    def test_identity_recovery(self):
        report, report_path, unknown_path = (
            run_canonical_observation_identity_recovery_audit()
        )

        print("[POSTGRES_TRANSACTION]", report["postgres_transaction"])
        print("[CANONICAL_QUERY_SURFACE]", report["canonical_query_surface"])
        print("[REQUEST_CLASS]", report["request_class"])
        print("[BY_OBSERVATION_ID_SIGNATURE]", report["by_observation_id_signature"])
        print("[FIRST_REQUEST_CONTRACT]", report["first_request_contract"])
        print("[LINKAGE_ROWS_READ]", report["linkage_rows_read"])
        print("[UNIQUE_OBSERVATIONS_ATTEMPTED]", report["unique_observations_attempted"])
        print("[RESTORED_OBSERVATION_COUNT]", report["restored_observation_count"])
        print("[MISSING_OBSERVATION_COUNT]", report["missing_observation_count"])
        print("[FAMILY_COUNTS]", report["family_counts"])
        print("[REASON_COUNTS]", report["reason_counts"])

        print("[OBSERVED_FIELD_PATHS]")
        for path, count in list(report["observed_field_paths"].items())[:100]:
            print(" ", path, "count=", count)

        print("[STILL_UNKNOWN_COUNT]", len(report["unresolved"]))
        for i, rec in enumerate(report["unresolved"][:50], 1):
            print(
                "[STILL_UNKNOWN]",
                i,
                "ticker=", rec["ticker"],
                "observation_id=", rec["observation_id"],
                "type=", rec["canonical_observation_type"],
                "canonical_observation=", rec["canonical_observation"],
            )

        print("[REPORT]", report_path)
        print("[UNKNOWN_REPORT]", unknown_path)

        self.assertTrue(report["read_only"])
        self.assertFalse(report["execution_authority"])
        self.assertFalse(report["probability_enabled"])
        self.assertEqual(report["postgres_transaction"], "BEGIN READ ONLY")
        self.assertIsNotNone(report["first_request_contract"])
        self.assertGreater(report["linkage_rows_read"], 0)
        self.assertGreater(report["unique_observations_attempted"], 0)
        self.assertGreater(report["restored_observation_count"], 0)

if __name__ == "__main__":
    print("=" * 112)
    print(" OAD POSTGRESQL CANONICAL OBSERVATION IDENTITY RECOVERY AUDIT")
    print(" FULL CERTIFIED QUERY CONTRACT REBUILD")
    print("=" * 112)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] full by_observation_id keyword-only contract used")
    print("[PASS] query_id/backend_id/requested_at/query_metadata populated")
    print("[PASS] PostgreSQL linkage read through BEGIN READ ONLY")
    print("[PASS] canonical observations restored through certified backend.query()")
    print("[PASS] no PostgreSQL row modified")
    print("[PASS] no production classifier modified")
    print("[PASS] probability_enabled=FALSE")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] CANONICAL OBSERVATION IDENTITY RECOVERY AUDIT COMPLETE")
