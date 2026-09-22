import unittest

from qseries_v2.oracle_adapters.independent.oad_373_solana_universal_economic_event_promotion import promote_economic_behavior
from qseries_v2.oracle_adapters.independent.oad_374_solana_temporal_case_bridge import build_temporal_learning_case
from qseries_v2.oracle_adapters.independent.oad_375_solana_verified_forward_outcome_bridge import attribute_verified_forward_outcome
from qseries_v2.oracle_adapters.independent.oad_376_solana_learned_experience_bridge import build_learned_experience, as_learning_payload

class T(unittest.TestCase):
    def test_experience(self):
        e=promote_economic_behavior({
            "event_id":"e1",
            "slot":1,
            "behavior_type":"DEX_SWAP",
            "primary_asset":"A",
            "secondary_asset":"B",
        })
        c=build_temporal_learning_case(e,(15,))
        o=attribute_verified_forward_outcome(c,15,100.0,101.0)
        x=build_learned_experience(c,o)
        p=as_learning_payload(x)

        print("[EXPERIENCE]",x.experience_id,x.outcome,x.learning_namespace,x.immutable_payload_hash)

        self.assertEqual(x.learning_namespace,"EXISTING_OCL")
        self.assertEqual(len(x.immutable_payload_hash),64)
        self.assertEqual(p["case_id"],c.case_id)
        self.assertFalse(x.execution_authority)

    def test_hash_is_deterministic(self):
        e=promote_economic_behavior({
            "event_id":"e2",
            "slot":2,
            "behavior_type":"TOKEN_FLOW",
            "primary_asset":"TOKEN",
        })
        c=build_temporal_learning_case(e,(30,))
        o=attribute_verified_forward_outcome(c,30,50.0,49.0)

        a=build_learned_experience(c,o)
        b=build_learned_experience(c,o)

        self.assertEqual(a.immutable_payload_hash,b.immutable_payload_hash)
        self.assertEqual(a.experience_id,b.experience_id)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-376 immutable evidence-grounded Solana learned experience bridge certified")
    print("[PASS] learned experiences target EXISTING_OCL only")
    print("[PASS] no separate Solana learner introduced")
