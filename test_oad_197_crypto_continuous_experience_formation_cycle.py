import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_197_crypto_continuous_experience_formation_cycle as m

class T(unittest.TestCase):
    def test_cycle_contract(self):
        candidate=SimpleNamespace(
            experience_id="crypto-exp:BTC:x",asset="BTC",snapshot_at="2026-08-30T00:00:00+00:00",
            cohort_state="FULL_COVERAGE",condition_vector=(),temporal_vector=(),
            evidence_state="CROSS_SOURCE_PRESENT",consistency_state="CONSISTENT",
            market_native_metrics=1,independent_chain_metrics=1,comparable_temporal_metrics=0,
            evidence_hash="a"*64,condition_hash="b"*64,experience_hash="c"*64,
            outcome_attached=False,probability=None,direction=None,execution_authority=False
        )
        lineage=SimpleNamespace(asset="BTC",lineage_hash="d"*64)
        runtime=SimpleNamespace(runtime_ready=True,snapshot_at="2026-08-30T00:00:00+00:00")
        persistence=SimpleNamespace(already_present=0,committed_new=1,exact_readback=1)
        with patch.object(m,"run_crypto_durable_temporal_intelligence",return_value=runtime), \
             patch.object(m,"build_crypto_historical_experience_candidates",return_value=(candidate,)), \
             patch.object(m,"verify_crypto_historical_experience_candidate",return_value=True), \
             patch.object(m,"build_crypto_experience_evidence_lineage",return_value=lineage), \
             patch.object(m,"verify_crypto_experience_evidence_lineage",return_value=True), \
             patch.object(m,"persist_crypto_experience_candidates",return_value=persistence):
            r=m.form_continuous_crypto_experience_cycle()
        print("[CANDIDATES]",r.candidates); print("[COMMITTED_NEW]",r.committed_new); print("[READY]",r.physical_ready)
        self.assertTrue(r.physical_ready)
        self.assertEqual(r.assets,("BTC",))
        self.assertFalse(r.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-197 continuous crypto experience-formation cycle contract certified")
