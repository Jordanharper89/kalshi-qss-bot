import unittest
from qseries_v2.oracle_intelligence_state.ois_026_universal_surveillance import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_026_universal_venue_surveillance_foundation())

    def test_entire_universe_required(self):
        self.assertTrue(build_venue_surveillance_policy("kalshi").entire_universe_required)

    def test_active_one_second(self):
        self.assertEqual(build_venue_surveillance_policy("kalshi").active_max_refresh_seconds,1.0)

    def test_no_execution(self):
        self.assertFalse(build_venue_surveillance_policy("kalshi").execution_authority)

if __name__=="__main__":
    print("="*72);print(" OIS-026 CERTIFICATION TEST");print(" UNIVERSAL VENUE SURVEILLANCE FOUNDATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Universal full-venue surveillance foundation certified")
    print("[DONE] OIS-026 CERTIFIED")
