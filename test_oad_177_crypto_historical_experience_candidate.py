import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_177_crypto_historical_experience_candidate import build_crypto_historical_experience_candidates,verify_crypto_historical_experience_candidate
class T(unittest.TestCase):
    def test_candidate(self):
        ch=SimpleNamespace(asset="BTC",source_family="bitcoin",metric_name="fastest_fee_rate",current_value=12,current_condition="ELEVATED",temporal_state="INCREASED",absolute_change=2,percent_change=20,comparable_history_present=True)
        p=SimpleNamespace(asset="BTC",evidence_state="CROSS_SOURCE_PRESENT",consistency_state="NO_EXPLICIT_CONTRADICTION",market_native_metrics=3,independent_chain_metrics=7)
        r=SimpleNamespace(snapshot_at="2026-08-29T02:00:00+00:00",cohort_state="FULL_COVERAGE",changes=(ch,),profiles=(p,))
        x=build_crypto_historical_experience_candidates(r)[0]
        print("[EXPERIENCE_ID]",x.experience_id)
        print("[COMPARABLE]",x.comparable_temporal_metrics)
        self.assertTrue(verify_crypto_historical_experience_candidate(x))
        self.assertFalse(x.outcome_attached)
        self.assertIsNone(x.probability)
        self.assertIsNone(x.direction)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-177 deterministic outcome-pending crypto experience candidate certified")
