from __future__ import annotations
import unittest
from datetime import datetime, timezone
from qseries_v2.observation_intelligence.oi_054_explanation_terminal_handoff_boundary import ExplanationTerminalHandoff
from qseries_v2.observation_intelligence.oi_055_terminal_explanation_session_adapter import TerminalExplanationSessionTurn
from qseries_v2.observation_intelligence.oi_057_explanation_response_coordinator import (
    OI_057_REVISION,OracleExplanationResponseCoordinator,verify_explanation_response_coordinator)

NOW=datetime(2026,8,11,18,0,tzinfo=timezone.utc)

def handoff(q="query.2"):
    return ExplanationTerminalHandoff(
        response_id="response.2",query_id=q,subject_hint="Astros strikeouts",
        completeness_status="complete",display_payload=("response",),
        handoff_hash="a"*64,read_only=True,terminal_mutation_allowed=False)

def prior():
    return TerminalExplanationSessionTurn(
        session_id="session.1",turn_number=1,query_id="query.1",response_id="response.1",
        subject_hint="Astros strikeouts",completeness_status="partial",display_payload=("prior",),
        received_at=NOW,turn_hash="b"*64,read_only=True)

class TestOI057(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_explanation_response_coordinator())
    def test_first_turn(self):
        r=OracleExplanationResponseCoordinator().coordinate(
            session_id="session.1",prior_turns=(),handoff=handoff("query.1"),received_at=NOW)
        self.assertEqual(r.turn.turn_number,1); self.assertEqual(r.context.turn_count,1)
    def test_followup_turn(self):
        r=OracleExplanationResponseCoordinator().coordinate(
            session_id="session.1",prior_turns=(prior(),),handoff=handoff(),received_at=NOW)
        self.assertEqual(r.turn.turn_number,2); self.assertEqual(r.context.turn_count,2)
        self.assertEqual(r.context.latest_query_id,"query.2")
    def test_context_preserved(self):
        r=OracleExplanationResponseCoordinator().coordinate(
            session_id="session.1",prior_turns=(prior(),),handoff=handoff(),received_at=NOW)
        self.assertEqual(r.context.latest_subject_hint,"Astros strikeouts")
        self.assertEqual(r.context.latest_completeness_status,"complete")
    def test_deterministic(self):
        c=OracleExplanationResponseCoordinator()
        a=c.coordinate(session_id="session.1",prior_turns=(prior(),),handoff=handoff(),received_at=NOW)
        b=c.coordinate(session_id="session.1",prior_turns=(prior(),),handoff=handoff(),received_at=NOW)
        self.assertEqual(a.response_hash,b.response_hash)
    def test_side_effects(self):
        x=OracleExplanationResponseCoordinator(); self.assertTrue(x.read_only)
        for n in ("network_allowed","persistence_allowed","publication_allowed","execution_allowed",
                  "qseries_execution_allowed","prediction_allowed","edge_score_allowed",
                  "probability_allowed","causal_claim_allowed","terminal_mutation_allowed"):
            self.assertFalse(getattr(x,n))

if __name__=="__main__":
    print("="*72); print(" OI-057 CERTIFICATION TEST"); print(" EXPLANATION RESPONSE COORDINATOR"); print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestOI057))
    if not r.wasSuccessful(): raise SystemExit(1)
    print(); print("[PASS] Build: OI-057"); print(f"[PASS] Revision: {OI_057_REVISION}")
    print("[PASS] First-turn and follow-up explanation responses coordinated deterministically")
    print("[PASS] Session turn numbering, latest query, subject, completeness state, and context lineage preserved")
    print("[PASS] Network, persistence, publication, prediction, scoring, causation, and execution disabled")
    print("[DONE] OI-057 CERTIFIED")
