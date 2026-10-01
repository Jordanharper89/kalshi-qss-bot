import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061a_shared_rpc_valve as q
class T(unittest.TestCase):
    def test_mode(self): self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
    def test_gap(self): self.assertGreaterEqual(q.MIN_RPC_GAP_SECONDS,.25)
if __name__=="__main__": unittest.main(verbosity=2)
