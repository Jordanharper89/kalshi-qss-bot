import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_059b_provider_contract_prebinding_gate as q
class T(unittest.TestCase):
    def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
    def test_contracts(self):self.assertTrue(callable(q.rc.quote_exact_in));self.assertTrue(callable(q.ow.quote_exact_in))
if __name__=="__main__":unittest.main(verbosity=2)
