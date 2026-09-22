import unittest
from qseries_v2.oracle_adapters.independent.oad_108_official_mlb_source_adapter import fetch_mlb_schedule
class T(unittest.TestCase):
    def test_physical(self):
        rows=fetch_mlb_schedule(timeout_seconds=20)
        print("[MLB_OBSERVATIONS]",len(rows))
        for x in rows[:5]: print("[MLB]",x.subject,x.source_id)
        self.assertTrue(all(x.provider=="statsapi.mlb.com" for x in rows))
        self.assertTrue(all(x.sport_family=="baseball" for x in rows))
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] physical official MLB acquisition completed")
    print("[PASS] read_only=TRUE execution_authority=FALSE")
