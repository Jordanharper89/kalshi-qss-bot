import unittest
from qseries_v2.oracle_pre_settlement_coverage import opc_045_repeated_presettlement_observation_physical_proof as m
class T(unittest.TestCase):
 def test_physical(self):
  self.assertTrue(m.verify_opc_045());x=m.physical_probe();self.assertTrue(x["plan_uses_index"]);self.assertGreater(x["checked"],0);self.assertTrue(x["read_only"]);self.assertFalse(x["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
