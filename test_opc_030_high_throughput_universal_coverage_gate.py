import unittest,inspect
from qseries_v2.oracle_pre_settlement_coverage import opc_030_high_throughput_universal_coverage_gate as m
class T(unittest.TestCase):
 def test_contract(self):
  self.assertTrue(m.verify_opc_030_high_throughput_universal_coverage_gate())
  s=inspect.getsource(m.run_high_throughput_coverage_cycle)
  self.assertIn("read_recent_canonical_market_freshness",s); self.assertIn("freshness=freshness",s)
if __name__=="__main__":unittest.main(verbosity=2)
