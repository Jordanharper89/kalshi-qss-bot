import unittest
from datetime import timezone
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_054_proven_current_trader_analytics as m

class T(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(m.OIAR_054_BUILD_ID,"OIAR-054")

    def test_timezone_parser(self):
        x=m._aware_datetime("2026-08-23 21:57:24.988199-05:00")
        self.assertIsNotNone(x.tzinfo)
        self.assertIsNotNone(x.utcoffset())
        self.assertEqual(x.tzinfo,timezone.utc)

    def test_physical(self):
        x=m.read_latest_current_trader_analytics()
        self.assertTrue(x)
        self.assertGreater(x["market_count"],0)
        self.assertTrue(x["read_only_source"])
        self.assertFalse(x["execution_authority"])

if __name__=="__main__":
    print("="*88)
    print(" OIAR-054 CERTIFICATION TEST")
    print(" PROVEN CURRENT TRADER ANALYTICS")
    print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] persisted observed_at restored to timezone-aware datetime")
    print("[PASS] proven current OIA analytics certified")
    print("[DONE] OIAR-054 CERTIFIED")
