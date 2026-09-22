from __future__ import annotations
import unittest
from qseries_v2.oracle_continuous_intake.oci_003_postgresql_read_contract import *

class TestOCI003(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_oci_003_postgresql_read_only_intake_contract())
    def test_query_is_parameterized(self):
        q=build_incremental_read_query("public","oracle_live_shadow","sequence_id",123,50)
        self.assertIn("%s",q.sql);self.assertEqual(q.params,(123,50));self.assertTrue(verify_read_only_sql(q.sql))
    def test_identifier_injection_rejected(self):
        with self.assertRaises(ValueError):build_incremental_read_query("public;drop table x","t","id",0)
    def test_limit_bounded(self):
        with self.assertRaises(ValueError):build_incremental_read_query("public","t","id",0,10001)
    def test_write_sql_rejected(self):
        self.assertFalse(verify_read_only_sql("DELETE FROM x"))
        self.assertFalse(verify_read_only_sql("SELECT 1; DROP TABLE x"))
    def test_read_only_transaction(self):
        self.assertEqual(read_only_session_commands(5000)[0],"BEGIN READ ONLY")

if __name__=="__main__":
    print("="*72);print(" OCI-003 CERTIFICATION TEST");print(" POSTGRESQL READ-ONLY INTAKE CONTRACT");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestOCI003))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Parameterized bounded SELECT-only PostgreSQL contract certified")
    print("[DONE] OCI-003 CERTIFIED")
