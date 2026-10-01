import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_064c_profit_runtime_launcher as q
class T(unittest.TestCase):
 def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
 def test_machine(self):self.assertIn("machine.serve",inspect.getsource(q.main))
if __name__=="__main__":unittest.main(verbosity=2)
