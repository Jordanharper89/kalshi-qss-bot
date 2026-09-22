import unittest
from qseries_v2.oracle_pre_settlement_coverage import opc_049_post_repair_settlement_cohort_read_model as m
class T(unittest.TestCase):
 def test_physical(self):
  self.assertTrue(m.verify_opc_049());x=m.physical_probe();self.assertIn("post_repair_settlements",x);self.assertTrue(x["read_only"]);self.assertFalse(x["probability_enabled"]);self.assertFalse(x["execution_authority"]);print("[PHYSICAL]",x)
if __name__=="__main__":unittest.main(verbosity=2)
