import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_036_mriya_exact_pump_meteora_binding as q
class T(unittest.TestCase):
    def test_exact_gate(self):
        s=inspect.getsource(q.resolve);self.assertIn('d.get("quote_mint")==pd.c.WSOL',s);self.assertIn('d.get("base_mint")==token',s)
    def test_four(self):self.assertEqual(q.MAX_BIND,4)
    def test_read_only(self):self.assertNotIn("sendTransaction",inspect.getsource(q))
if __name__=="__main__":unittest.main(verbosity=2)
