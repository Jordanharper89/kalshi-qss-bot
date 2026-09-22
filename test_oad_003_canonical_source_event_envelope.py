import unittest
from qseries_v2.oracle_adapters.oad_003_canonical_event import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_oad_003_canonical_source_event_envelope())

    def test_deterministic(self):
        a = build_canonical_source_event("a","s","e","trade",1,2,1,{"x":1})
        b = build_canonical_source_event("a","s","e","trade",1,2,1,{"x":1})
        self.assertEqual(a.envelope_hash, b.envelope_hash)

    def test_nonmonotonic_rejected(self):
        with self.assertRaises(ValueError):
            build_canonical_source_event("a","s","e","trade",2,1,1,{})

if __name__ == "__main__":
    print("=" * 72)
    print(" OAD-003 CERTIFICATION TEST")
    print(" CANONICAL SOURCE EVENT ENVELOPE")
    print("=" * 72)
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Deterministic canonical source-event envelope certified")
    print("[DONE] OAD-003 CERTIFIED")
