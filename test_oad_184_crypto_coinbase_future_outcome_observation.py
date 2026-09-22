import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_184_crypto_coinbase_future_outcome_observation import build_crypto_future_outcome
class T(unittest.TestCase):
    def test_real_contract(self):
        exp=SimpleNamespace(experience_id="e1",asset="BTC",condition_vector=(("coinbase","spot_price",100.0,"OBSERVED"),))
        maturity=SimpleNamespace(mature=True,experience=exp,horizon_seconds=60)
        obs=SimpleNamespace(subject="BTC-USD",payload={"price":"105"},observed_at="2026-08-29T02:01:01Z",source_id="coinbase:BTC-USD:ticker:1",provenance_hash="a"*64)
        x=build_crypto_future_outcome(maturity,obs)
        print("[RETURN_PERCENT]",x.return_percent)
        print("[OUTCOME_TYPE]",x.outcome_observation.outcome_type)
        self.assertAlmostEqual(x.return_percent,5.0)
        self.assertEqual(len(x.outcome_observation.outcome_hash),64)
if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-184 verified Coinbase future outcome observation certified")
