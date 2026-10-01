import unittest,tempfile,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_033_mriya_live_token_venue_matrix as q
class T(unittest.TestCase):
    def test_constants(self):self.assertTrue(q.WSOL.startswith("So111"))
    def test_read_only(self):
        import inspect
        self.assertNotIn("sendTransaction",inspect.getsource(q))
if __name__=="__main__":unittest.main(verbosity=2)
