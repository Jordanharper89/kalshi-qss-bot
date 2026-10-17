import unittest
from qseries_v2.oracle_execution.solana_atomic_executor import mry_007_candidate_hydrator as m

class T(unittest.TestCase):
    def test_exports(self):
        self.assertTrue(callable(m.hydrate_candidate))
        self.assertTrue(callable(m._token_amount))

    def test_pair_type_available(self):
        self.assertTrue(hasattr(m.pd,"PairState"))

if __name__=="__main__":
    unittest.main(verbosity=2)
