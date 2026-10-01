import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_029b_mriya_real_hotset_coverage_gap as q
class T(unittest.TestCase):
    def test_wsol_excluded(self):self.assertIn("m!=WSOL",inspect.getsource(q.inspect))
    def test_actual_runtime_compare(self):self.assertIn("p.m.prepare",inspect.getsource(q.inspect))
if __name__=="__main__":unittest.main(verbosity=2)
