import unittest
from qseries_v2.oracle_execution.solana_atomic_executor import mry_008_execution_readiness as m

class T(unittest.TestCase):
    def test_exact_canary(self):
        self.assertEqual(m.CANARY_LAMPORTS,10_000_000)

    def test_api(self):
        self.assertTrue(callable(m.prepare_forward))
        self.assertTrue(callable(m.install_forward))

if __name__=="__main__":
    unittest.main(verbosity=2)
