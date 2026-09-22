import unittest
from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_021_physical_kalshi_credential_auth_loader())
    def test_missing(self):
        with self.assertRaises(RuntimeError): load_kalshi_credentials(root=".",environ={})
    def test_redaction(self):
        c=KalshiCredentialConfig("id","-----BEGIN PRIVATE KEY-----x","environment")
        self.assertNotIn("private_key_pem",redact_credential_config(c))
if __name__=="__main__":
    print("="*72);print(" OAD-021 CERTIFICATION TEST");print(" PHYSICAL KALSHI CREDENTIAL + AUTH LOADER");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Local-only Kalshi credential loading/redaction certified");print("[DONE] OAD-021 CERTIFIED")
