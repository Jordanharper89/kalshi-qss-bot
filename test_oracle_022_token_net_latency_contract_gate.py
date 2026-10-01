import inspect,unittest
from qseries_v2.oracle_execution import oracle_022_token_net_latency_contract_gate as q22

class T(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(q22.EXECUTION_AUTHORITY)
        self.assertTrue(q22.PAPER_ONLY)
        self.assertFalse(q22.REAL_MONEY_MOVED)
    def test_exact_net_received_target(self):
        s=inspect.getsource(q22.run)
        self.assertIn('q18.q14.engine.net_received',s)
    def test_multiple_amounts(self):
        self.assertEqual(q22.GROSS_VALUES,(1000,10000,100000,1000000))
    def test_no_private_key_or_broadcast(self):
        s=inspect.getsource(q22)
        self.assertNotIn('QSB_SOLANA_PRIVATE_KEY',s)
        self.assertNotIn('sendTransaction',s)

if __name__=='__main__':
    unittest.main(verbosity=2)
