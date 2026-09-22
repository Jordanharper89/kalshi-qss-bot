import unittest
from qseries_v2.oracle_intelligence_analytics_runtime import oiar_080_current_observation_source_independence_probe as m
class T(unittest.TestCase):
 def test_physical(self):
  x=m.physical_probe();self.assertGreater(x["rows_read"],0);self.assertEqual(x["rows_read"],x["market_native_rows"]+x["independent_candidate_rows"]);self.assertFalse(x["probability_enabled"]);self.assertFalse(x["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
