import inspect,unittest
from qseries_v2.oracle_execution import oracle_023_persistent_token_net_worker as q23
class T(unittest.TestCase):
    def test_safety(self): self.assertFalse(q23.EXECUTION_AUTHORITY); self.assertTrue(q23.PAPER_ONLY); self.assertFalse(q23.REAL_MONEY_MOVED)
    def test_persistent_process(self):
        s=inspect.getsource(q23.TokenNetWorker); self.assertIn('subprocess.Popen',s); self.assertNotIn('subprocess.run',s)
    def test_hot_patch(self): self.assertIn('q18.token_net=token_net',inspect.getsource(q23.install_hot_token_net))
    def test_no_private_key_or_broadcast(self):
        s=inspect.getsource(q23); self.assertNotIn('QSB_SOLANA_PRIVATE_KEY',s); self.assertNotIn('sendTransaction',s)
if __name__=='__main__': unittest.main(verbosity=2)
