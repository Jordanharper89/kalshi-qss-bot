import inspect,unittest
from qseries_v2.oracle_execution import oracle_024_persistent_token_net_live_cutover as q24

class T(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(q24.EXECUTION_AUTHORITY)
        self.assertTrue(q24.PAPER_ONLY)
        self.assertFalse(q24.REAL_MONEY_MOVED)

    def test_patch_targets_exact_seam(self):
        s=inspect.getsource(q24.install)
        self.assertIn("q23.install_hot_token_net()",s)
        self.assertIn("q18.token_net is not q23.token_net",s)

    def test_all_pair_prewarm(self):
        s=inspect.getsource(q24.prewarm_exact_tokens)
        self.assertIn('state=q19.persistent.m.prepare(Path.cwd())',s)
        self.assertIn('q23.worker().warm(token)',s)
        self.assertIn('q23.worker().refresh_epoch()',s)

    def test_q20_reused(self):
        s=inspect.getsource(q24.run_q20)
        self.assertIn('getattr(q20,"run",None)',s)
        self.assertIn('getattr(q20,"main",None)',s)

    def test_no_private_key_or_broadcast(self):
        s=inspect.getsource(q24)
        self.assertNotIn("QSB_SOLANA_PRIVATE_KEY",s)
        self.assertNotIn("sendTransaction",s)

if __name__=="__main__":
    unittest.main(verbosity=2)
