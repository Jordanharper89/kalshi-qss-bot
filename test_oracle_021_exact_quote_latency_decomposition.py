import inspect,unittest
from qseries_v2.oracle_execution import oracle_021_exact_quote_latency_decomposition as q21

class T(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(q21.EXECUTION_AUTHORITY)
        self.assertTrue(q21.PAPER_ONLY)
        self.assertFalse(q21.REAL_MONEY_MOVED)
    def test_sizes(self):
        self.assertEqual(q21.SIZES,(0.001,0.010,0.050))
    def test_exact_components_measured(self):
        s=inspect.getsource(q21.run)
        self.assertIn("w.buy",s)
        self.assertIn("w.sell",s)
        self.assertIn("core.dlmm_quote_snapshot",s)
    def test_no_private_key_or_broadcast(self):
        s=inspect.getsource(q21)
        self.assertNotIn("QSB_SOLANA_PRIVATE_KEY",s)
        self.assertNotIn("sendTransaction",s)
if __name__=="__main__":
    unittest.main(verbosity=2)
