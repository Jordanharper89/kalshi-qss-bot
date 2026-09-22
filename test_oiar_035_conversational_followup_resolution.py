import unittest
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_035_conversational_followup_resolution as m
class T(unittest.TestCase):
 def test_today(self):self.assertTrue(m.classify_followup("is this for today?"));self.assertEqual(m.followup_kind("is this for today?"),"time")
 def test_first(self):self.assertTrue(m.classify_followup("what about the first one?"));self.assertEqual(m.ordinal_index("what about the first one?"),0)
 def test_why(self):self.assertTrue(m.classify_followup("why?"))
if __name__=="__main__":
 print("="*88);print(" OIAR-035 CERTIFICATION TEST");print(" CONVERSATIONAL FOLLOW-UP RESOLUTION");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] trader follow-up routing certified");print("[DONE] OIAR-035 CERTIFIED")
