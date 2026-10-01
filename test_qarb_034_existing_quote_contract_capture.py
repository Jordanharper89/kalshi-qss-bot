import unittest,inspect
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_034_existing_quote_contract_capture as q
class T(unittest.TestCase):
    def test_targets(self):
        s=" ".join(q.MODULES);self.assertIn("live_account_stream",s);self.assertIn("raydium_cpmm",s);self.assertIn("raydium_clmm",s)
    def test_no_execution(self):self.assertNotIn("sendTransaction",inspect.getsource(q))
if __name__=="__main__":unittest.main(verbosity=2)
