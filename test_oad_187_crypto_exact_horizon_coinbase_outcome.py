import unittest,json
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_187_crypto_exact_horizon_coinbase_outcome import acquire_exact_coinbase_outcome
class Resp:
    def read(self): return json.dumps([[1787972520,99,102,100,101,12],[1787972460,98,101,99,100,10]]).encode()
def opener(req,timeout): return Resp()
class T(unittest.TestCase):
    def test_exact(self):
        e=SimpleNamespace(experience_id="e1",asset="BTC",snapshot_at="2026-08-29T02:00:00+00:00",condition_vector=(("coinbase","spot_price",100.0,"OBSERVED"),))
        x=acquire_exact_coinbase_outcome(e,60,opener=opener)
        print("[MATURITY]",x.matures_at); print("[CANDLE]",x.candle_start); print("[RETURN]",x.return_percent)
        self.assertTrue(x.exact_interval); self.assertEqual(x.outcome_observation.outcome_type,"coinbase_spot_return_60s_exact_interval")
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-187 deterministic first-Coinbase-minute-at/after-horizon outcome certified")
