import unittest
from qseries_v2.oracle_intelligence_analytics_runtime import oiar_078_current_repeated_history_reasoning_brief as m
class T(unittest.TestCase):
 def test_physical(self):
  x=m.physical_probe();self.assertGreater(x["lines"],5);self.assertEqual(x["header"],"ORACLE CURRENT REPEATED-HISTORY REASONING BRIEF");self.assertFalse(x["probability_enabled"]);self.assertFalse(x["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
