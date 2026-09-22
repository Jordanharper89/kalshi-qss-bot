import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_179_crypto_experience_candidate_postgresql_persistence import canonicalize_crypto_experience_candidate
class T(unittest.TestCase):
    def test_canonical(self):
        c=SimpleNamespace(experience_id="crypto-exp:BTC:abc",asset="BTC",snapshot_at="2026-08-29T02:00:00+00:00",cohort_state="FULL_COVERAGE",
            condition_vector=(("bitcoin","x",1.0,"OBSERVED"),),temporal_vector=(("bitcoin","x","UNCHANGED",0.0,0.0,True),),
            evidence_state="CROSS_SOURCE_PRESENT",consistency_state="NO_EXPLICIT_CONTRADICTION",market_native_metrics=3,independent_chain_metrics=7,
            comparable_temporal_metrics=1,evidence_hash="a"*64,condition_hash="b"*64,experience_hash="c"*64)
        l=SimpleNamespace(lineage_hash="d"*64)
        x=canonicalize_crypto_experience_candidate(c,l)
        p=dict(x.payload)
        print("[SOURCE_ID]",x.source_id)
        print("[OUTCOME_ATTACHED]",p["outcome_attached"])
        self.assertEqual(x.source_id,"source.crypto.experience.btc")
        self.assertFalse(p["outcome_attached"])
        self.assertIsNone(p["probability"])
        self.assertFalse(x.execution_allowed)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-179 immutable PostgreSQL experience-candidate contract certified")
