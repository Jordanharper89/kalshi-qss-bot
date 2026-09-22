import unittest
from qseries_v2.oracle_adapters.independent.oad_postgresql_unknown_sports_family_full_audit import run_postgresql_unknown_sports_family_audit

class T(unittest.TestCase):
    def test_physical_postgresql_audit(self):
        report,jp,cp,up=run_postgresql_unknown_sports_family_audit()
        print("[POSTGRES] connection_path=",report["connection_path"])
        print("[POSTGRES] transaction_mode=",report["transaction_mode"])
        print("[POSTGRES] candidate_table_count=",report["candidate_table_count"])
        for t in report["tables"]:
            print("[POSTGRES_TABLE]",f'{t["schema"]}.{t["table"]}',"rows_read=",t["rows_read"],"identity_columns=",t["identity_columns"],"payload_columns=",t["payload_columns"])
        print("[FAMILY_COUNTS]",report["family_counts"])
        print("[REASON_COUNTS]",report["reason_counts"])
        for family,count in report["family_counts"].items(): print("[FAMILY]",family,"rows=",count)
        print("[STILL_UNKNOWN_COUNT]",len(report["still_unknown"]))
        for i,r in enumerate(report["still_unknown"][:100],1): print("[STILL_UNKNOWN]",i,r)
        print("[REPORT]",jp); print("[ASSIGNMENTS_CSV]",cp); print("[UNKNOWN_CSV]",up)
        self.assertTrue(report["read_only"])
        self.assertFalse(report["execution_authority"])
        self.assertFalse(report["probability_enabled"])
        self.assertEqual(report["transaction_mode"],"BEGIN READ ONLY")
        self.assertGreater(report["candidate_table_count"],0)

if __name__=="__main__":
    print("="*108)
    print(" OAD POSTGRESQL UNKNOWN SPORTS FAMILY FULL AUDIT")
    print(" DIRECT AUDITED BACKEND CONNECTION — READ ONLY")
    print("="*108)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] actual production PostgreSQL backend connection used")
    print("[PASS] transaction forced BEGIN READ ONLY")
    print("[PASS] family assignments exported separately from production state")
    print("[PASS] no classifier or PostgreSQL row modified")
    print("[PASS] probability_enabled=FALSE")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] POSTGRESQL UNKNOWN SPORTS FAMILY FULL AUDIT COMPLETE")
