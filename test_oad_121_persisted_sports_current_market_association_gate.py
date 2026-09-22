import unittest
from unittest.mock import patch
from types import SimpleNamespace
import qseries_v2.oracle_adapters.independent.oad_121_persisted_sports_current_market_association_gate as m

class T(unittest.TestCase):
    def test_candidate_only_gate(self):
        row=SimpleNamespace(
            observation_id="o1",
            source_id="source.independent.mlb:game:1",
            payload=(("subject","Houston Astros at New York Mets"),("independent_evidence",True)),
        )
        cohort=SimpleNamespace(rows=(row,),cohort_size=1)
        candidate=SimpleNamespace(market_id="KXTEST",candidate_only=True)
        with patch.object(m,"load_persisted_authoritative_sports_cohort",return_value=cohort), \
             patch.object(m,"fetch_current_market_sports_candidates",
                          return_value=(({"ticker":"KXTEST"},),((SimpleNamespace(observation_id="o1"),(candidate,)),))):
            r=m.run_persisted_sports_current_market_association_gate(root=".")
        print("[PERSISTED]",r.persisted_observations)
        print("[CURRENT_MARKETS]",r.current_markets)
        print("[ASSOCIATION_CANDIDATES]",r.association_candidates)
        print("[READY_FOR_REASONING_EVIDENCE_COMPARISON]",r.ready_for_reasoning_evidence_comparison)
        self.assertEqual(r.association_candidates,1)
        self.assertTrue(r.ready_for_reasoning_evidence_comparison)
        self.assertFalse(r.execution_authority)

if __name__=="__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-121 persisted sports current-market association gate certified")
    print("[NOTE] associations remain candidate_only; no direction/probability is manufactured")
