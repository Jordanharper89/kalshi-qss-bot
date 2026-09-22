import unittest
from qseries_v2.oracle_scientific_reasoning.osr_008_temporal_sequence import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_008_temporal_precedence_event_sequence_reasoning())
    def test_deterministic(self):
        a=TemporalEvent("a",1,"a"*64);b=TemporalEvent("b",2,"b"*64)
        self.assertEqual(analyze_temporal_sequence((a,b)).sequence_hash,analyze_temporal_sequence((b,a)).sequence_hash)
    def test_tie_not_strict(self):
        a=TemporalEvent("a",1,"a"*64);b=TemporalEvent("b",1,"b"*64)
        self.assertFalse(analyze_temporal_sequence((a,b)).strictly_ordered)
    def test_duplicate(self):
        a=TemporalEvent("a",1,"a"*64)
        with self.assertRaises(ValueError): analyze_temporal_sequence((a,a))

if __name__=="__main__":
    print("="*72);print(" OSR-008 CERTIFICATION TEST");print(" TEMPORAL PRECEDENCE + EVENT SEQUENCE REASONING");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Deterministic temporal precedence and event-sequence reasoning certified")
    print("[DONE] OSR-008 CERTIFIED")
