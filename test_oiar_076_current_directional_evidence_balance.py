import unittest
from qseries_v2.oracle_intelligence_analytics_runtime import oiar_076_current_directional_evidence_balance as m
class T(unittest.TestCase):
 def test_physical(self):
  x=m.physical_probe();self.assertGreater(x["markets"],0);self.assertFalse(x["probability_enabled"]);self.assertFalse(x["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
