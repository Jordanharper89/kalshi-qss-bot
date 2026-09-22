import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_198_crypto_continuous_exact_outcome_maturation as m

class T(unittest.TestCase):
    def test_market_not_finalized_is_hold_not_failure(self):
        p=SimpleNamespace(experience_id="e1",asset="BTC",snapshot_at="2026-08-30T00:00:00+00:00")
        rb=SimpleNamespace(records=(p,))
        maturity=SimpleNamespace(experience=p)
        with patch.object(m,"read_persisted_crypto_experiences",return_value=rb), \
             patch.object(m,"read_crypto_learned_case_history",return_value=()), \
             patch.object(m,"select_mature_crypto_experiences",return_value=(maturity,)), \
             patch.object(m,"acquire_exact_coinbase_outcome",
                          side_effect=RuntimeError("no Coinbase one-minute candle at/after maturity")):
            r=m.mature_continuous_crypto_outcomes()
        print("[MATURE_PENDING]",r.mature_pending)
        print("[EXACT_OUTCOMES]",r.exact_outcomes)
        print("[HELD_MARKET_NOT_FINALIZED]",r.held_market_not_finalized)
        print("[READY]",r.physical_ready)
        self.assertEqual(r.mature_pending,1)
        self.assertEqual(r.exact_outcomes,0)
        self.assertEqual(r.held_market_not_finalized,1)
        self.assertTrue(r.physical_ready)

    def test_real_runtime_error_still_raises(self):
        p=SimpleNamespace(experience_id="e1",asset="BTC",snapshot_at="2026-08-30T00:00:00+00:00")
        rb=SimpleNamespace(records=(p,))
        maturity=SimpleNamespace(experience=p)
        with patch.object(m,"read_persisted_crypto_experiences",return_value=rb), \
             patch.object(m,"read_crypto_learned_case_history",return_value=()), \
             patch.object(m,"select_mature_crypto_experiences",return_value=(maturity,)), \
             patch.object(m,"acquire_exact_coinbase_outcome",
                          side_effect=RuntimeError("Coinbase HTTP 503")):
            with self.assertRaisesRegex(RuntimeError,"503"):
                m.mature_continuous_crypto_outcomes()

    def test_exact_outcome_still_passes(self):
        p=SimpleNamespace(experience_id="e2",asset="ETH",snapshot_at="2026-08-30T00:00:00+00:00")
        rb=SimpleNamespace(records=(p,))
        maturity=SimpleNamespace(experience=p)
        outcome=SimpleNamespace(experience_id="e2",asset="ETH")
        with patch.object(m,"read_persisted_crypto_experiences",return_value=rb), \
             patch.object(m,"read_crypto_learned_case_history",return_value=()), \
             patch.object(m,"select_mature_crypto_experiences",return_value=(maturity,)), \
             patch.object(m,"acquire_exact_coinbase_outcome",return_value=outcome):
            r=m.mature_continuous_crypto_outcomes()
        print("[OUTCOME_READY]",r.exact_outcomes)
        self.assertEqual(r.exact_outcomes,1)
        self.assertEqual(r.held_market_not_finalized,0)
        self.assertTrue(r.physical_ready)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-198 foundational finalized-candle hold rebuild certified")
