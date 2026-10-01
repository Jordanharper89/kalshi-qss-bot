import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_028b_mriya_executor_flow_decoder as q
class T(unittest.TestCase):
    def test_account_level_netting(self):
        rows=[{"side":"pre","account_index":1,"mint":"A","amount":5},{"side":"post","account_index":1,"mint":"A","amount":2},{"side":"pre","account_index":2,"mint":"B","amount":1},{"side":"post","account_index":2,"mint":"B","amount":4}]
        d=q.deltas(rows);self.assertEqual(d[(1,"A")],-3);self.assertEqual(d[(2,"B")],3)
    def test_closed_flow(self):
        p={"rows":[{"signature":"s","slot":1,"err":None,"program_ids":[],"token_balance_rows":[{"side":"pre","account_index":1,"mint":"A","amount":1},{"side":"post","account_index":1,"mint":"A","amount":1}]}]}
        self.assertEqual(q.decode(p)["mint_counts"],{})
if __name__=="__main__":unittest.main(verbosity=2)
