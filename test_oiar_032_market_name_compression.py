import unittest
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_032_market_name_compression as m
class T(unittest.TestCase):
 def test_identity(self):self.assertEqual(m.OIAR_032_BUILD_ID,"OIAR-032")
 def test_combo(self):
  x=m.compress_market_name({"market_title":"yes Philadelphia,yes Cleveland,yes Boston,yes Milwaukee,yes Pittsburgh"})
  self.assertEqual(x,"Philadelphia + Cleveland + Boston + Milwaukee + 1 more")
 def test_not_raw(self):
  x=m.compress_market_name({"market_title":"yes Both Teams To Score,yes Atletico,yes Real Madrid,no Valencia wins"})
  self.assertNotIn("yes ",x.lower());self.assertNotIn("no ",x.lower())
if __name__=="__main__":
 print("="*88);print(" OIAR-032 CERTIFICATION TEST");print(" MARKET NAME COMPRESSION");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] trader-readable market-name compression certified");print("[DONE] OIAR-032 CERTIFIED")
