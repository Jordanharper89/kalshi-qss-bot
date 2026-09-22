import unittest
from unittest.mock import patch
from types import SimpleNamespace
import qseries_v2.oracle_adapters.independent.oad_116_authoritative_sports_production_persistence_certification as m

class T(unittest.TestCase):
    def test_certification_accounting(self):
        src=SimpleNamespace(
            cohort_size=15,already_present=10,missing_before_write=5,committed_new=5,
            exact_readback=15,providers=("statsapi.mlb.com",),execution_authority=False)
        with patch.object(m,"persist_current_authoritative_sports",return_value=src):
            r=m.run_authoritative_sports_production_certification(root=".")
        print("[CERTIFIED]",r["certified"])
        print("[COHORT_SIZE]",r["cohort_size"])
        print("[COMMITTED_NEW]",r["committed_new"])
        print("[EXACT_READBACK]",r["exact_readback"])
        self.assertTrue(r["certified"])
        self.assertEqual(r["exact_readback"],15)
        self.assertFalse(r["execution_authority"])

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-116 production persistence certification contract certified")
    print("[NOTE] run_authoritative_sports_production_certification performs physical network+PostgreSQL certification")
