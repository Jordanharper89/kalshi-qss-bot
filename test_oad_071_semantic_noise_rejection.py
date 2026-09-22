import unittest
from qseries_v2.oracle_adapters.independent.oad_071_semantic_noise_rejection import *
class T(unittest.TestCase):
 def test_generic_new_rejected(self): self.assertNotIn("new",semantic_tokens("new new latest update"))
 def test_domain_term_retained(self): self.assertIn("bitcoin",semantic_tokens("Bitcoin price threshold"))
 def test_phrase(self): self.assertIn("bitcoin-price",strong_phrases("Bitcoin price threshold"))
 def test_verify(self): self.assertTrue(verify_oad_071())
if __name__=="__main__":
 print("="*88);print(" OAD-071 CERTIFICATION TEST");print(" SEMANTIC NOISE REJECTION");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] Generic collision terms including 'new' rejected")
 print("[DONE] OAD-071 CERTIFIED")
