import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_062c1_mriya_shared_rpc_binding_repair as q
class T(unittest.TestCase):
 def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
 def test_binding(self):self.assertTrue(any("oad_148" in x for x in q.bind_all_rpc()))
if __name__=="__main__":unittest.main(verbosity=2)
