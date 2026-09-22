import unittest

from qseries_v2.oracle_adapters.independent.oad_219_crypto_maturity_adaptive_state_resolution import (
    resolve_maturity_adaptive_state,
    verify_frozen_maturity_adaptive_contracts,
)

class T(unittest.TestCase):
    def test_frozen_contracts(self):
        self.assertTrue(verify_frozen_maturity_adaptive_contracts())

    def test_resolution(self):
        r=resolve_maturity_adaptive_state(
            evidence_count=252,
            independent_sources=3,
            consistency=.70,
            contradiction_rate=.20,
            calibration_quality=.50,
            performance_history=(.10,.20,.15),
        )
        print("[MATURITY_BAND]",r.maturity.maturity_band)
        print("[MATURITY_SCORE]",r.maturity.maturity_score)
        print("[ADAPTIVE_WEIGHT]",r.adaptive_weight.adjusted_weight)
        print("[MATURITY_HASH]",r.maturity_state_hash)
        print("[ADAPTIVE_HASH]",r.adaptive_weight_state_hash)

        self.assertEqual(len(r.maturity_state_hash),64)
        self.assertEqual(len(r.adaptive_weight_state_hash),64)
        self.assertTrue(r.frozen_contracts_verified)
        self.assertFalse(r.probability_enabled)
        self.assertFalse(r.direction_enabled)
        self.assertFalse(r.execution_authority)

    def test_invalid_history_still_fails_closed(self):
        with self.assertRaises(ValueError):
            resolve_maturity_adaptive_state(1,1,.5,.2,.5,())

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-219 frozen OCL maturity/adaptive state resolution certified")
