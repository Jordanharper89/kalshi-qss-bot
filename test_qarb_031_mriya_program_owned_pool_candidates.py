import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_031_mriya_program_owned_pool_candidates as q
class T(unittest.TestCase):
    def test_owner_gate(self):
        s=inspect.getsource(q.resolve);self.assertIn('x.get("owner")!=pid',s)
    def test_batched_accounts(self):
        s=inspect.getsource(q.resolve);self.assertIn("getMultipleAccounts",s);self.assertIn("100",s)
    def test_read_only(self):self.assertNotIn("sendTransaction",inspect.getsource(q))
if __name__=="__main__":unittest.main(verbosity=2)
