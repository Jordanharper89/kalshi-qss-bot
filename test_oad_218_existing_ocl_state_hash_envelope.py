import unittest
from qseries_v2.oracle_adapters.independent.oad_218_existing_ocl_state_hash_envelope import (
    envelope,certified_state_hash,
)

class T(unittest.TestCase):
    def test_deterministic_hash(self):
        a=envelope("maturity",{"b":2,"a":1})
        b=envelope("maturity",{"a":1,"b":2})
        print("[HASH]",a.state_hash)
        self.assertEqual(a.state_hash,b.state_hash)
        self.assertEqual(len(a.state_hash),64)
        self.assertFalse(a.fabricated)
        self.assertFalse(a.probability_enabled)
        self.assertFalse(a.execution_authority)

    def test_missing_state_rejected(self):
        with self.assertRaises(ValueError):
            certified_state_hash("calibration",None)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-218 deterministic physical-state hash envelope certified")
