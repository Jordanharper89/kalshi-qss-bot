import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_169_crypto_temporal_condition_change_evaluator import evaluate_crypto_temporal_condition_changes
def s(v,c="OBSERVED"):
    return SimpleNamespace(asset="ETH",source_family="ethereum",metric_name="gas_price_wei",value=v,condition=c,observed_at=None)
class T(unittest.TestCase):
    def test_change(self):
        r=evaluate_crypto_temporal_condition_changes((s(120),),(s(100),))[0]
        print("[TEMPORAL]",r.temporal_state,r.percent_change)
        self.assertEqual(r.temporal_state,"INCREASED")
        self.assertEqual(r.percent_change,20.0)
        n=evaluate_crypto_temporal_condition_changes((s(120),),())[0]
        self.assertEqual(n.temporal_state,"NO_COMPARABLE_HISTORY")
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-169 temporal condition change evaluator certified")
