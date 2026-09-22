\

import unittest
from qseries_v2.oracle_adapters.independent.oad_363_solana_physical_postgresql_readback_adapter import *

class T(unittest.TestCase):
    def test_injected_exact(self):
        x=physical_readback_probe(("1","2"),lambda ids:[{"observation_id":"1"},{"observation_id":"2"}])
        print("[READBACK-ADAPTER]",x.reader_symbol,x.found_ids,x.missing_ids,x.exact)
        self.assertTrue(x.exact)
    def test_injected_missing(self):
        x=physical_readback_probe(("1","2"),lambda ids:[{"observation_id":"1"}])
        self.assertFalse(x.exact)
        self.assertEqual(x.missing_ids,("2",))

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-363 physical PostgreSQL readback adapter contract certified")

