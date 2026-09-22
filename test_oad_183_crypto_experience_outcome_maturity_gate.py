import unittest
from datetime import datetime,timezone
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_183_crypto_experience_outcome_maturity_gate import evaluate_crypto_experience_maturity
class T(unittest.TestCase):
    def test_horizon(self):
        e=SimpleNamespace(snapshot_at="2026-08-29T02:00:00+00:00")
        early=evaluate_crypto_experience_maturity(e,60,datetime(2026,8,29,2,0,30,tzinfo=timezone.utc))
        mature=evaluate_crypto_experience_maturity(e,60,datetime(2026,8,29,2,1,0,tzinfo=timezone.utc))
        print("[EARLY]",early.state)
        print("[MATURE]",mature.state)
        self.assertFalse(early.mature)
        self.assertTrue(mature.mature)
if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-183 future-horizon maturity gate certified")
