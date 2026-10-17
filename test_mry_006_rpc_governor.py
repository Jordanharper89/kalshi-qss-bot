import unittest
from qseries_v2.oracle_execution.solana_atomic_executor import mry_006_rpc_governor as m

class T(unittest.TestCase):
    def test_429_backoff(self):
        g=m.RpcGovernor(base=10,maximum=100)
        limited,x=g.failure(RuntimeError("HTTP 429 Too Many Requests"))
        self.assertTrue(limited)
        self.assertGreater(x,10)

    def test_success_recovers(self):
        g=m.RpcGovernor(base=10,maximum=100)
        g.failure(RuntimeError("429"))
        self.assertGreaterEqual(g.success(),10)

    def test_classifier(self):
        self.assertTrue(m.is_rate_limited(Exception("server rate limit")))

if __name__=="__main__":
    unittest.main(verbosity=2)
