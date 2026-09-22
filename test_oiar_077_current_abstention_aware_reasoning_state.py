import unittest
from qseries_v2.oracle_intelligence_analytics_runtime import oiar_077_current_abstention_aware_reasoning_state as m
class T(unittest.TestCase):
 def test_physical(self):
  x=m.physical_probe();self.assertEqual(x["markets"],x["ready"]+x["observe"]+x["abstain"]);self.assertFalse(x["probability_enabled"]);self.assertFalse(x["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
