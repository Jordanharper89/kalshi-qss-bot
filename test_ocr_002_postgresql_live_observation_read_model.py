import unittest
from qseries_v2.oracle_continuous_reasoning.ocr_002_live_observation_read_model import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_ocr_002_postgresql_live_observation_read_model())
    def test_identifier_rejected(self):
        with self.assertRaises(ValueError): quote_sql_identifier("x;drop")
    def test_limit_contract(self): self.assertTrue(LiveObservationReadResult("s","t",tuple()).read_only)
if __name__=="__main__":
    print("="*72);print(" OCR-002 CERTIFICATION TEST");print(" POSTGRESQL LIVE OBSERVATION READ MODEL");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] SELECT-only live observation read model certified")
    print("[DONE] OCR-002 CERTIFIED")
