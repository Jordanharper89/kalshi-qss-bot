import unittest
from qseries_v2.oracle_adapters.kalshi.oad_007_transport_auth import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_007_kalshi_transport_auth_boundary())
    def test_query_stripped(self): self.assertEqual(signing_message(5,"GET","/trade-api/v2/markets?limit=1"),"5GET/trade-api/v2/markets")
    def test_no_orders(self): self.assertFalse(build_kalshi_transport_auth_boundary().order_methods_allowed)
if __name__=="__main__":
    print("="*72);print(" OAD-007 CERTIFICATION TEST");print(" KALSHI TRANSPORT + AUTHENTICATION BOUNDARY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi REST/WebSocket authentication boundary certified read-only");print("[DONE] OAD-007 CERTIFIED")
