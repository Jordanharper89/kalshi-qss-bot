import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_170_crypto_cross_source_consistency_profile import build_crypto_cross_source_consistency_profiles
class T(unittest.TestCase):
    def test_profile(self):
        s=(
            SimpleNamespace(asset="SOL",market_native_reference=True,independent_evidence=False),
            SimpleNamespace(asset="SOL",market_native_reference=False,independent_evidence=True),
        )
        r=build_crypto_cross_source_consistency_profiles(s)[2]
        print("[EVIDENCE_STATE]",r.evidence_state)
        print("[CONSISTENCY]",r.consistency_state)
        print("[CONTRADICTIONS]",r.contradictions)
        self.assertEqual(r.evidence_state,"CROSS_SOURCE_PRESENT")
        self.assertEqual(r.contradictions,())
        self.assertIsNone(r.direction); self.assertIsNone(r.probability)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-170 cross-source consistency profile certified")
