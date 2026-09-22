import unittest

from qseries_v2.oracle_adapters.independent.oad_220_scientific_reasoning_state_hash_registry import (
    REQUIRED_STATE_HASHES,
    CAPABILITY_BY_HASH,
    build_state_hash_registry,
)

class T(unittest.TestCase):
    def test_missing_remains_missing(self):
        r=build_state_hash_registry({
            "maturity":{"band":"immature","score":0.09},
            "adaptive_weight":{"weight":0.06},
        })
        print("[HASHES]",r.hashes)
        print("[MISSING]",r.missing)
        self.assertFalse(r.complete)
        self.assertFalse(r.fabricated)
        self.assertIn("calibration_state_hash",r.missing)
        self.assertIn("source_reliability_state_hash",r.missing)
        self.assertNotIn("maturity_state_hash",r.missing)
        self.assertNotIn("adaptive_weight_state_hash",r.missing)
        self.assertFalse(r.probability_enabled)
        self.assertFalse(r.direction_enabled)
        self.assertFalse(r.execution_authority)

    def test_complete_only_with_all_real_states(self):
        states={
            CAPABILITY_BY_HASH[name]:{"physical":name}
            for name in REQUIRED_STATE_HASHES
        }
        r=build_state_hash_registry(states)
        self.assertTrue(r.complete)
        self.assertEqual(len(r.hashes),8)
        for value in r.hashes.values():
            self.assertEqual(len(value),64)

    def test_none_is_truthful_hold(self):
        r=build_state_hash_registry(None)
        self.assertFalse(r.complete)
        self.assertEqual(r.missing,REQUIRED_STATE_HASHES)
        self.assertEqual(r.hashes,{})

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-220 truthful Scientific Reasoning state-hash registry certified")
