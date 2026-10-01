import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_030_mriya_dex_instruction_account_capture as q
class T(unittest.TestCase):
    def test_account_normalize(self):
        self.assertEqual(q._accounts({"accounts":[0,"B",2]},["A","X","C"]),["A","B","C"])
    def test_pid(self):
        self.assertEqual(q._pid({"programIdIndex":1},["A","P"]), "P")
    def test_read_only(self):
        import inspect
        self.assertNotIn("sendTransaction",inspect.getsource(q))
if __name__=="__main__":unittest.main(verbosity=2)
