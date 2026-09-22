import unittest
from datetime import datetime,timezone
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_034_temporal_relevance as m
class T(unittest.TestCase):
 def test_unknown_is_not_today(self):self.assertEqual(m.temporal_relevance({},datetime(2026,8,24,12,tzinfo=timezone.utc))["label"],"UNKNOWN")
 def test_today_requires_time(self):self.assertEqual(m.temporal_relevance({"event_start":"2026-08-24T20:00:00+00:00"},datetime(2026,8,24,12,tzinfo=timezone.utc))["label"],"TODAY")
if __name__=="__main__":
 print("="*88);print(" OIAR-034 CERTIFICATION TEST");print(" TEMPORAL RELEVANCE");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] no-guess temporal grounding certified");print("[DONE] OIAR-034 CERTIFIED")
