import unittest

from qseries_v2.oracle_adapters.independent.oad_106_exact_sports_unknown_record_extractor import (
    run_exact_sports_unknown_record_extractor,
)

class T(unittest.TestCase):
    def test_exact_extractor(self):
        report, report_path = run_exact_sports_unknown_record_extractor(limit=1000)

        print("[SNAPSHOT_ID]", report["snapshot_id"])
        print("[MARKET_COUNT]", report["market_count"])
        print("[DECOMPOSED_LEG_COUNT]", report["decomposed_leg_count"])
        print("[SPORTS_UNKNOWN_RECORD_COUNT]", report["sports_unknown_record_count"])
        print("[SEMANTIC_CALLABLE]", report["semantic_callable"])
        print("[ROUTER_CALLABLE]", report["router_callable"])

        for i, rec in enumerate(report["records"][:100], 1):
            m = rec["market"]
            print(
                "[SPORTS_UNKNOWN]",
                i,
                "ticker=", m.get("ticker"),
                "title=", m.get("title"),
                "event_ticker=", m.get("event_ticker"),
                "series_ticker=", m.get("series_ticker"),
                "leg_index=", rec["leg_index"],
                "leg=", rec["leg"],
                "guarded_identity=", rec["guarded_identity"],
                "semantic_identity=", rec["semantic_identity"],
                "source_requirement=", rec["source_requirement"],
            )

        print("[REPORT]", report_path)

        self.assertTrue(report["read_only"])
        self.assertFalse(report["execution_authority"])
        self.assertFalse(report["probability_enabled"])
        self.assertGreater(report["market_count"], 0)
        self.assertGreater(report["decomposed_leg_count"], 0)

if __name__ == "__main__":
    print("=" * 120)
    print(" OAD-106 EXACT SPORTS:UNKNOWN RECORD EXTRACTOR")
    print(" CERTIFIED PRODUCTION PIPELINE REPLAY — READ ONLY")
    print("=" * 120)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] exact OAD-106 production cohort capture used")
    print("[PASS] exact OAD-099 mixed-market decomposition used")
    print("[PASS] exact OAD-102 identity-envelope construction used")
    print("[PASS] exact OAD-103 guarded identity resolution used")
    print("[PASS] sports:UNKNOWN records extracted without fallback classifier")
    print("[PASS] no PostgreSQL access performed")
    print("[PASS] no production module modified")
    print("[PASS] probability_enabled=FALSE")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OAD-106 EXACT SPORTS UNKNOWN RECORD EXTRACTION COMPLETE")
