import unittest
from qseries_v2.oracle_adapters.independent.oad_058_federal_register_adapter import *
class T(unittest.TestCase):
    def test_physical_federal_register(self):
        rows=acquire_federal_register_documents(limit=3)
        self.assertGreater(len(rows),0)
        self.assertTrue(all(x.source_id=="federalregister.gov" for x in rows))
if __name__=="__main__":
    print("="*72); print(" OAD-058 PHYSICAL CERTIFICATION TEST"); print(" FEDERAL REGISTER AUTHORITATIVE ACQUISITION"); print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Physical Federal Register API observations acquired")
    print("[DONE] OAD-058 CERTIFIED")
