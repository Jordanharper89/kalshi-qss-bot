import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061b_two_ws_valves_paper_lane as q
class T(unittest.TestCase):
    def test_mode(self): self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
    def test_two(self): self.assertEqual(len(q.two_valves(list(range(10)))),2)
    def test_all(self): self.assertEqual(sum(map(len,q.two_valves(list(range(11))))),11)
if __name__=="__main__": unittest.main(verbosity=2)
