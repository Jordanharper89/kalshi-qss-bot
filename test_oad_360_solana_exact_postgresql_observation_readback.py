import unittest
from qseries_v2.oracle_adapters.independent.oad_360_solana_exact_postgresql_observation_readback import *

class T(unittest.TestCase):
    def test_exact(self):
        r=exact_postgresql_observation_readback(
            ("a","b"),
            lambda ids:[{"observation_id":"a"},{"observation_id":"b"}]
        )
        print("[READBACK]",r.found_ids,r.missing_ids,r.exact)
        self.assertTrue(r.exact)

    def test_missing(self):
        r=exact_postgresql_observation_readback(
            ("a","b"),
            lambda ids:[{"observation_id":"a"}]
        )
        self.assertFalse(r.exact)
        self.assertEqual(r.missing_ids,("b",))

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-360 exact observation-ID PostgreSQL readback contract certified")
