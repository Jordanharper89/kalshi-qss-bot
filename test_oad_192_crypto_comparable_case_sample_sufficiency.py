import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_192_crypto_comparable_case_sample_sufficiency import assess_comparable_case_sufficiency
class T(unittest.TestCase):
    def test_states(self):
        stats=(
            SimpleNamespace(asset="BTC",horizon_seconds=60,condition_signature=(("x",),),sample_size=3),
            SimpleNamespace(asset="ETH",horizon_seconds=60,condition_signature=(("y",),),sample_size=25),
            SimpleNamespace(asset="SOL",horizon_seconds=60,condition_signature=(("z",),),sample_size=120),
        )
        rows=assess_comparable_case_sufficiency(stats)
        print("[STATES]",tuple(x.sufficiency_state for x in rows))
        print("[NEEDED]",tuple(x.cases_needed_to_next_state for x in rows))
        self.assertEqual(rows[0].sufficiency_state,"INSUFFICIENT")
        self.assertEqual(rows[1].sufficiency_state,"DEVELOPING")
        self.assertEqual(rows[2].sufficiency_state,"MATURE_DESCRIPTIVE")
        self.assertFalse(any(x.predictive_probability_eligible for x in rows))
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-192 explicit comparable-case sample sufficiency certified")
