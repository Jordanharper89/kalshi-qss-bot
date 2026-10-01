import inspect,unittest
from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25

class T(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(q25.EXECUTION_AUTHORITY)
        self.assertTrue(q25.PAPER_ONLY)
        self.assertFalse(q25.REAL_MONEY_MOVED)

    def test_certified_single_hydration_reused(self):
        s=inspect.getsource(q25.prepare_once)
        self.assertIn("q60b2.prepare_once",s)
        self.assertIn("ORACLE025_NO_EXACT_PAIRS_AFTER_SINGLE_HYDRATION",s)

    def test_cached_prepare_bound_into_q19(self):
        s=inspect.getsource(q25.bind_cached_state)
        self.assertIn("q60b.m.prepare=cached_prepare",s)
        self.assertIn("q19.persistent.m.prepare=cached_prepare",s)

    def test_token_net_prewarm(self):
        s=inspect.getsource(q25.install_hot_math_and_prewarm)
        self.assertIn("q23.install_hot_token_net()",s)
        self.assertIn("q23.worker().warm(token)",s)
        self.assertIn("q23.worker().refresh_epoch()",s)

    def test_q20_reused(self):
        s=inspect.getsource(q25.invoke_q20)
        self.assertIn('getattr(q20,"run",None)',s)
        self.assertIn('getattr(q20,"main",None)',s)

    def test_no_private_key_or_broadcast(self):
        s=inspect.getsource(q25)
        self.assertNotIn("QSB_SOLANA_PRIVATE_KEY",s)
        self.assertNotIn("sendTransaction",s)

if __name__=="__main__":
    unittest.main(verbosity=2)
