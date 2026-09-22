import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_174_crypto_historical_condition_sequence_and_prior_state import (
    select_latest_prior_comparable_states,build_crypto_condition_sequences
)
def s(t,v):
    return SimpleNamespace(asset="BTC",source_family="bitcoin",metric_name="fastest_fee_rate",observed_at=t,value=v,condition="OBSERVED")
class T(unittest.TestCase):
    def test_prior_and_sequence(self):
        hist=(s("2026-08-29T00:00:00+00:00",10),s("2026-08-29T00:30:00+00:00",12))
        cur=(s("2026-08-29T01:00:00+00:00",15),)
        p=select_latest_prior_comparable_states(cur,hist)
        q=build_crypto_condition_sequences(hist)
        print("[PRIOR]",p[0].value)
        print("[SEQUENCE_POINTS]",q[0].point_count)
        self.assertEqual(p[0].value,12)
        self.assertEqual(q[0].point_count,2)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-174 historical sequence and exact prior-state selection certified")
