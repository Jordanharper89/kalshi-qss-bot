from __future__ import annotations
import unittest
from datetime import datetime, timezone
from qseries_v2.observation_intelligence.oi_054_explanation_terminal_handoff_boundary import ExplanationTerminalHandoff
from qseries_v2.observation_intelligence.oi_055_terminal_explanation_session_adapter import (
    OI_055_REVISION, TerminalExplanationSessionAdapter,
    verify_terminal_explanation_session_adapter,
)

NOW = datetime(2026,8,11,16,0,tzinfo=timezone.utc)

def handoff():
    return ExplanationTerminalHandoff(
        response_id="response.astros", query_id="query.astros",
        subject_hint="Astros strikeouts", completeness_status="partial",
        display_payload=("Oracle Evidence Explanation","STATUS: PARTIAL"),
        handoff_hash="a"*64, read_only=True, terminal_mutation_allowed=False,
    )

class TestOI055(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(verify_terminal_explanation_session_adapter())
    def test_adapt(self):
        turn = TerminalExplanationSessionAdapter().adapt(
            session_id="session.1", turn_number=1,
            handoff=handoff(), received_at=NOW)
        self.assertEqual(turn.turn_number,1)
        self.assertEqual(turn.query_id,"query.astros")
    def test_payload_preserved(self):
        turn = TerminalExplanationSessionAdapter().adapt(
            session_id="session.1", turn_number=1,
            handoff=handoff(), received_at=NOW)
        self.assertEqual(turn.display_payload,handoff().display_payload)
    def test_deterministic(self):
        a = TerminalExplanationSessionAdapter().adapt(
            session_id="session.1", turn_number=1,
            handoff=handoff(), received_at=NOW)
        b = TerminalExplanationSessionAdapter().adapt(
            session_id="session.1", turn_number=1,
            handoff=handoff(), received_at=NOW)
        self.assertEqual(a.turn_hash,b.turn_hash)
    def test_side_effects(self):
        x=TerminalExplanationSessionAdapter()
        self.assertTrue(x.read_only)
        for name in ("network_allowed","persistence_allowed","publication_allowed",
                     "execution_allowed","qseries_execution_allowed","prediction_allowed",
                     "edge_score_allowed","probability_allowed","causal_claim_allowed",
                     "terminal_mutation_allowed"):
            self.assertFalse(getattr(x,name))

if __name__ == "__main__":
    print("="*72); print(" OI-055 CERTIFICATION TEST"); print(" TERMINAL EXPLANATION SESSION ADAPTER"); print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestOI055))
    if not r.wasSuccessful(): raise SystemExit(1)
    print(); print("[PASS] Build: OI-055"); print(f"[PASS] Revision: {OI_055_REVISION}")
    print("[PASS] Terminal explanation handoff adapted into deterministic session turns")
    print("[PASS] Session identity, turn number, query, response, subject, status, and display payload preserved")
    print("[PASS] Network, persistence, publication, prediction, scoring, causation, and execution disabled")
    print("[DONE] OI-055 CERTIFIED")
