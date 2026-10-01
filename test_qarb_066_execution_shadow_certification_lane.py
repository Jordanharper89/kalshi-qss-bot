import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_066_execution_shadow_certification_lane as q
class T(unittest.TestCase):
 def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
 def test_native_shadow_preserved(self):self.assertIsNot(q._NATIVE_SHADOW,q.qf.PaperSimulationLane)
 def test_both_lanes(self):
  s=inspect.getsource(q.CertificationLane);self.assertIn("PaperSimulationLane",s);self.assertIn("_NATIVE_SHADOW",s)
 def test_live_only_shadow(self):
  s=inspect.getsource(q.CertificationLane.submit);self.assertIn('age is None',s);self.assertIn('float(age)>750',s)
 def test_no_new_runtime(self):self.assertNotIn("async def serve(",inspect.getsource(q))
if __name__=="__main__":unittest.main(verbosity=2)
