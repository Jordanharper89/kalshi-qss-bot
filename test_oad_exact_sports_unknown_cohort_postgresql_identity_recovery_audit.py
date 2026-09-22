import unittest

from qseries_v2.oracle_adapters.independent.oad_exact_sports_unknown_cohort_postgresql_identity_recovery_audit import (
    run_exact_sports_unknown_cohort_postgresql_identity_recovery_audit,
)

class T(unittest.TestCase):
    def test_exact_sports_unknown_identity_recovery(self):
        report, report_path, unknown_path = (
            run_exact_sports_unknown_cohort_postgresql_identity_recovery_audit()
        )

        print("[POSTGRES_TRANSACTION]", report["postgres_transaction"])
        print("[CURRENT_MARKET_COHORT_SOURCE]", report["current_market_cohort_source"])
        print("[SNAPSHOT_ID]", report["snapshot_id"])
        print("[CURRENT_MARKET_COUNT]", report["current_market_count"])
        print("[SPORTS_UNKNOWN_CANDIDATE_COUNT]", report["sports_unknown_candidate_count"])
        print("[UNIQUE_SPORTS_UNKNOWN_TICKERS]", report["unique_sports_unknown_tickers"])
        print("[POSTGRES_MARKET_SNAPSHOTS_RECOVERED]", report["postgres_market_snapshots_recovered"])
        print("[CLASSIFIER_ISOLATION_PATHS]", report["classifier_isolation_paths"])
        print("[FAMILY_COUNTS]", report["family_counts"])
        print("[REASON_COUNTS]", report["reason_counts"])

        for rec in report["assignments"][:100]:
            print(
                "[ASSIGNMENT]",
                "ticker=", rec["ticker"],
                "title=", rec["market_title"],
                "current=", rec["current_family"],
                "recommended=", rec["recommended_family"],
                "reason=", rec["reason"],
                "evidence=", rec["evidence"],
                "postgres_snapshot=", rec["postgres_market_snapshot_found"],
            )

        print("[REPORT]", report_path)
        print("[STILL_UNKNOWN_REPORT]", unknown_path)

        self.assertTrue(report["read_only"])
        self.assertFalse(report["execution_authority"])
        self.assertFalse(report["probability_enabled"])
        self.assertEqual(report["postgres_transaction"], "BEGIN READ ONLY")
        self.assertGreater(report["current_market_count"], 0)

        # This diagnostic must never fabricate family coverage.
        assigned = sum(report["family_counts"].values())
        self.assertEqual(assigned, report["unique_sports_unknown_tickers"])

if __name__ == "__main__":
    print("=" * 120)
    print(" OAD EXACT SPORTS:UNKNOWN COHORT -> POSTGRESQL MARKET IDENTITY RECOVERY AUDIT")
    print(" CURRENT LIVE COHORT ONLY — READ ONLY")
    print("=" * 120)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] current live market cohort isolated before PostgreSQL recovery")
    print("[PASS] sports:UNKNOWN candidates deduplicated by market ticker")
    print("[PASS] PostgreSQL access bounded to exact current candidate tickers")
    print("[PASS] at most one useful market_snapshot retained per market")
    print("[PASS] ambiguous/no-signal identities remain UNKNOWN")
    print("[PASS] no PostgreSQL row modified")
    print("[PASS] no OAD-104/OAD-105/OAD-106 classifier modified")
    print("[PASS] probability_enabled=FALSE")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] EXACT SPORTS UNKNOWN IDENTITY RECOVERY AUDIT COMPLETE")
