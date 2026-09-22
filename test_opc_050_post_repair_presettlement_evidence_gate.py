import unittest
from qseries_v2.oracle_pre_settlement_coverage import opc_050_post_repair_presettlement_evidence_gate as m
class T(unittest.TestCase):
 def test_physical(self):
  self.assertTrue(m.verify_opc_050());x=m.physical_probe();self.assertTrue(x["plan_uses_index"]);self.assertTrue(x["read_only"]);self.assertFalse(x["probability_enabled"]);self.assertFalse(x["execution_authority"]);print("[PHYSICAL]",x)
if __name__=="__main__":unittest.main(verbosity=2)
