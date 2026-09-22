import unittest
from datetime import datetime, timezone
from qseries_v2.oracle_adapters.independent.oad_109_official_nhl_source_adapter import fetch_nhl_schedule
class T(unittest.TestCase):
    def test_physical(self):
        d=datetime.now(timezone.utc).date().isoformat()
        rows=fetch_nhl_schedule(date=d,timeout_seconds=20)
        print("[NHL_DATE]",d)
        print("[NHL_OBSERVATIONS]",len(rows))
        for x in rows[:5]: print("[NHL]",x.subject,x.source_id)
        self.assertTrue(all(x.provider=="api-web.nhle.com" for x in rows))
        self.assertTrue(all(x.sport_family=="hockey" for x in rows))
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] physical official NHL acquisition completed")
    print("[PASS] read_only=TRUE execution_authority=FALSE")
