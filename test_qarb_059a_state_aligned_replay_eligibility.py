import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_059a_state_aligned_replay_eligibility as q
class T(unittest.TestCase):
    def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
    def test_state(self):
        self.assertEqual(q.state_evidence({"sqrt_price_x64":1,"slot":2}),(True,True))
if __name__=="__main__":unittest.main(verbosity=2)
