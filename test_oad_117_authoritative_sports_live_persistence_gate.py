import unittest
from unittest.mock import patch
import qseries_v2.oracle_adapters.independent.oad_117_authoritative_sports_live_persistence_gate as m

class T(unittest.TestCase):
    def test_accounting_contract(self):
        fixture={"certified":True,"cohort_size":15,"already_present":10,"committed_new":5,
                 "exact_readback":15,"providers":("statsapi.mlb.com",),
                 "read_only":True,"probability_enabled":False,"execution_authority":False}
        with patch.object(m,"run_authoritative_sports_production_certification",return_value=fixture):
            r=m.run_live_authoritative_sports_persistence_gate(root=".")
        print("[CERTIFIED]",r.certified)
        print("[COHORT_SIZE]",r.cohort_size)
        print("[ALREADY_PRESENT]",r.already_present)
        print("[COMMITTED_NEW]",r.committed_new)
        print("[EXACT_READBACK]",r.exact_readback)
        self.assertTrue(r.certified)
        self.assertEqual(r.already_present+r.committed_new,r.cohort_size)
        self.assertEqual(r.exact_readback,r.cohort_size)
        self.assertFalse(r.execution_authority)

if __name__=="__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-117 live persistence gate contract certified")
    print("[PHYSICAL] Run production function to exercise live MLB/NHL + PostgreSQL path")
