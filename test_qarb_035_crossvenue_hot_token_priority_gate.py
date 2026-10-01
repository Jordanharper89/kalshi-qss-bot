import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_035_crossvenue_hot_token_priority_gate as q
class T(unittest.TestCase):
    def test_paths(self):self.assertTrue(str(q.OUT).endswith("mriya_crossvenue_priority.json"))
if __name__=="__main__":unittest.main(verbosity=2)
