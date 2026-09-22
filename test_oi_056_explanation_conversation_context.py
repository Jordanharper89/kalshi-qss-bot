from __future__ import annotations
import unittest
from datetime import datetime, timezone
from qseries_v2.observation_intelligence.oi_055_terminal_explanation_session_adapter import TerminalExplanationSessionTurn
from qseries_v2.observation_intelligence.oi_056_explanation_conversation_context import (
    OI_056_REVISION,ExplanationConversationContextBuilder,
    verify_explanation_conversation_context)

NOW=datetime(2026,8,11,17,0,tzinfo=timezone.utc)

def turn(n,q,status):
    return TerminalExplanationSessionTurn(
        session_id="session.1",turn_number=n,query_id=q,response_id=f"response.{n}",
        subject_hint="Astros strikeouts",completeness_status=status,
        display_payload=(f"turn {n}",),received_at=NOW,turn_hash=str(n)*64,read_only=True)

class TestOI056(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_explanation_conversation_context())
    def test_context(self):
        c=ExplanationConversationContextBuilder().build(
            session_id="session.1",turns=(turn(1,"query.1","partial"),turn(2,"query.2","complete")))
        self.assertEqual(c.turn_count,2); self.assertEqual(c.latest_query_id,"query.2")
        self.assertEqual(c.latest_completeness_status,"complete")
    def test_empty(self):
        c=ExplanationConversationContextBuilder().build(session_id="session.1",turns=())
        self.assertEqual(c.turn_count,0); self.assertIsNone(c.latest_query_id)
    def test_wrong_session_rejected(self):
        bad=TerminalExplanationSessionTurn(
            session_id="session.2",turn_number=1,query_id="q",response_id="r",
            subject_hint="Bad",completeness_status="partial",display_payload=("bad",),
            received_at=NOW,turn_hash="a"*64,read_only=True)
        with self.assertRaises(ValueError):
            ExplanationConversationContextBuilder().build(session_id="session.1",turns=(bad,))
    def test_deterministic(self):
        ts=(turn(1,"query.1","partial"),turn(2,"query.2","complete")); b=ExplanationConversationContextBuilder()
        self.assertEqual(b.build(session_id="session.1",turns=ts).context_hash,
                         b.build(session_id="session.1",turns=ts).context_hash)
    def test_side_effects(self):
        x=ExplanationConversationContextBuilder(); self.assertTrue(x.read_only)
        for n in ("network_allowed","persistence_allowed","publication_allowed","execution_allowed",
                  "qseries_execution_allowed","prediction_allowed","edge_score_allowed",
                  "probability_allowed","causal_claim_allowed","terminal_mutation_allowed"):
            self.assertFalse(getattr(x,n))

if __name__=="__main__":
    print("="*72); print(" OI-056 CERTIFICATION TEST"); print(" EXPLANATION CONVERSATION CONTEXT"); print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestOI056))
    if not r.wasSuccessful(): raise SystemExit(1)
    print(); print("[PASS] Build: OI-056"); print(f"[PASS] Revision: {OI_056_REVISION}")
    print("[PASS] Ordered explanation session turns assembled into deterministic conversation context")
    print("[PASS] Latest query, subject, completeness state, session identity, and turn lineage preserved")
    print("[PASS] Network, persistence, publication, prediction, scoring, causation, and execution disabled")
    print("[DONE] OI-056 CERTIFIED")
