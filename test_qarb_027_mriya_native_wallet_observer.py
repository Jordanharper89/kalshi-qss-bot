import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_027_mriya_native_wallet_observer as q
class T(unittest.TestCase):
    def test_target(self):
        self.assertEqual(q.TARGET,"MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X")
    def test_token_map(self):
        rows=[{"owner":q.TARGET,"mint":"A","uiTokenAmount":{"uiAmountString":"2.5"}},
              {"owner":"X","mint":"A","uiTokenAmount":{"uiAmountString":"99"}}]
        self.assertEqual(q._token_map(rows),{"A":2.5})
    def test_read_only(self):
        import inspect
        s=inspect.getsource(q)
        for bad in ("sendTransaction","signTransaction","private_key"):
            self.assertNotIn(bad,s)
        print("[PASS] native observer is read-only")
if __name__=="__main__": unittest.main(verbosity=2)
