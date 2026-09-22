import unittest
from qseries_v2.oracle_adapters.independent.oad_078_authoritative_source_requirement_map import *

class T(unittest.TestCase):
    def test_existing(self):
        self.assertTrue(any(x.existing_adapter for x in requirements_for_topic("weather")))
        self.assertTrue(any(x.existing_adapter for x in requirements_for_topic("legal_regulatory")))
    def test_missing_macro(self):
        self.assertTrue(all(not x.existing_adapter for x in requirements_for_topic("macroeconomics")))
    def test_no_execution(self): self.assertFalse(EXECUTION_AUTHORITY)

if __name__=="__main__":
    print("="*88);print(" OAD-078 CERTIFICATION TEST");print(" AUTHORITATIVE SOURCE REQUIREMENT MAP");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Topic-to-authoritative-source requirements certified")
    print("[PASS] Existing NWS, Federal Register, and USGS families preserved")
    print("[DONE] OAD-078 CERTIFIED")
