import unittest,inspect
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_036_trader_card_presentation_cutover as m
class T(unittest.TestCase):
 def test_identity(self):self.assertEqual(m.OIAR_036_BUILD_ID,"OIAR-036")
 def test_no_scan(self):self.assertNotIn("oracle_canonical_observations",inspect.getsource(m))
 def test_readable(self):
  rows=({"market_title":"yes Philadelphia,yes Cleveland,yes Boston,yes Milwaukee,yes Pittsburgh","market_id":"x","trader_takeaway":"NO EDGE RIGHT NOW","direction":"NEUTRAL","why":"Live evidence is weak.","risk":"MODERATE","setup_status":"NO_CONFIRMED_EDGE"},)
  out=m.render_trader_cards(rows,2);text="\n".join(out)
  self.assertIn("Philadelphia + Cleveland",text);self.assertNotIn("yes Philadelphia,yes Cleveland",text)
  follow="\n".join(m.render_followup("is this for today?"));self.assertIn("cannot prove",follow)
if __name__=="__main__":
 print("="*88);print(" OIAR-036 CERTIFICATION TEST");print(" TRADER CARD PRESENTATION CUTOVER");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] readable trader-card and follow-up cutover certified");print("[DONE] OIAR-036 CERTIFIED")
