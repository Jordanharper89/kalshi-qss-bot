import unittest
from qseries_v2.oracle_adapters.kalshi.oad_027_event_intake_pump import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_027_continuous_real_market_event_intake_pump())
    def test_non_market_ignored(self):
        x=pump_market_messages(({"type":"subscribed"},),100)
        self.assertEqual(x.accepted,0)
if __name__=="__main__":
    print("="*72);print(" OAD-027 CERTIFICATION TEST");print(" CONTINUOUS REAL MARKET-EVENT INTAKE PUMP");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Continuous Kalshi market-event intake/sequence pump certified");print("[DONE] OAD-027 CERTIFIED")
