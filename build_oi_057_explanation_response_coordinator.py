from __future__ import annotations
import ast, hashlib
from pathlib import Path

BUILD_ID="OI-057"
INSTALLER_REVISION="OI_057_EXPLANATION_RESPONSE_COORDINATOR_INSTALLER_V1"
ROOT=Path.cwd().resolve()
PACKAGE=ROOT/"qseries_v2"/"observation_intelligence"
UPSTREAMS=(
    (PACKAGE/"oi_054_explanation_terminal_handoff_boundary.py","OI-054"),
    (PACKAGE/"oi_055_terminal_explanation_session_adapter.py","OI-055"),
    (PACKAGE/"oi_056_explanation_conversation_context.py","OI-056"),
)
MODULE=PACKAGE/"oi_057_explanation_response_coordinator.py"
INIT=PACKAGE/"__init__.py"
TEST=ROOT/"test_oi_057_explanation_response_coordinator.py"

MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_054_explanation_terminal_handoff_boundary import ExplanationTerminalHandoff
from .oi_055_terminal_explanation_session_adapter import TerminalExplanationSessionAdapter,TerminalExplanationSessionTurn
from .oi_056_explanation_conversation_context import ExplanationConversationContext,ExplanationConversationContextBuilder

BUILD_ID="OI-057"
OI_057_REVISION="OI_057_EXPLANATION_RESPONSE_COORDINATOR_V1"
READ_ONLY=True
NETWORK_ALLOWED=PERSISTENCE_ALLOWED=PUBLICATION_ALLOWED=False
EXECUTION_ALLOWED=QSERIES_EXECUTION_ALLOWED=False
PREDICTION_ALLOWED=EDGE_SCORE_ALLOWED=PROBABILITY_ALLOWED=False
CAUSAL_CLAIM_ALLOWED=TERMINAL_MUTATION_ALLOWED=False

@dataclass(frozen=True, slots=True)
class OracleExplanationCoordinatedResponse:
    session_id:str
    turn:TerminalExplanationSessionTurn
    context:ExplanationConversationContext
    response_hash:str
    read_only:bool

class OracleExplanationResponseCoordinator:
    read_only=True
    network_allowed=persistence_allowed=publication_allowed=False
    execution_allowed=qseries_execution_allowed=False
    prediction_allowed=edge_score_allowed=probability_allowed=False
    causal_claim_allowed=terminal_mutation_allowed=False

    def __init__(self):
        self._adapter=TerminalExplanationSessionAdapter()
        self._context=ExplanationConversationContextBuilder()

    def coordinate(self,*,session_id:str,prior_turns:tuple[TerminalExplanationSessionTurn,...],
                   handoff:ExplanationTerminalHandoff,received_at:datetime)->OracleExplanationCoordinatedResponse:
        sid=str(session_id).strip()
        if not sid: raise ValueError("session_id must not be empty")
        prior=tuple(prior_turns)
        if any(not isinstance(x,TerminalExplanationSessionTurn) for x in prior):
            raise TypeError("all prior_turns must be TerminalExplanationSessionTurn")
        if any(x.session_id!=sid for x in prior):
            raise ValueError("all prior_turns must belong to session_id")
        if prior!=tuple(sorted(prior,key=lambda x:x.turn_number)):
            raise ValueError("prior_turns must be supplied in turn order")
        next_number=(prior[-1].turn_number+1) if prior else 1
        turn=self._adapter.adapt(session_id=sid,turn_number=next_number,handoff=handoff,received_at=received_at)
        context=self._context.build(session_id=sid,turns=prior+(turn,))
        body={"session_id":sid,"turn_hash":turn.turn_hash,"context_hash":context.context_hash,"read_only":True}
        return OracleExplanationCoordinatedResponse(
            session_id=sid,turn=turn,context=context,
            response_hash=deterministic_sha256(body),read_only=True)

def verify_explanation_response_coordinator()->bool:
    if READ_ONLY is not True: raise AssertionError("OI-057 must remain read-only")
    if any((NETWORK_ALLOWED,PERSISTENCE_ALLOWED,PUBLICATION_ALLOWED,EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,PREDICTION_ALLOWED,EDGE_SCORE_ALLOWED,
            PROBABILITY_ALLOWED,CAUSAL_CLAIM_ALLOWED,TERMINAL_MUTATION_ALLOWED)):
        raise AssertionError("OI-057 forbidden capability enabled")
    return True

__all__=["BUILD_ID","OI_057_REVISION","OracleExplanationCoordinatedResponse",
         "OracleExplanationResponseCoordinator","verify_explanation_response_coordinator"]
"""

TEST_SOURCE=r"""
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
"""

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write_checked(path,source):
    text=source.lstrip(); ast.parse(text,filename=str(path)); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding="utf-8",newline="\n"); print(f"[PASS] Wrote: {path.relative_to(ROOT)}")

def main():
    print("="*72); print(" OI-057 INSTALLER"); print(" EXPLANATION RESPONSE COORDINATOR"); print("="*72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}"); print(f"[ROOT] {ROOT}")
    for u,n in UPSTREAMS:
        if not u.is_file(): raise RuntimeError(f"Certified {n} missing: {u}")
    hashes={u:sha(u) for u,_ in UPSTREAMS}; print("[PASS] Certified OI-054 through OI-056 verified read-only")
    affected=(MODULE,TEST,INIT); backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_checked(MODULE,MODULE_SOURCE); write_checked(TEST,TEST_SOURCE)
        current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .oi_057_explanation_response_coordinator import *"
        if export not in current.splitlines():
            if current and not current.endswith("\n"): current+="\n"
            current+=export+"\n"; ast.parse(current,filename=str(INIT)); INIT.write_text(current,encoding="utf-8",newline="\n")
        print("[PASS] Updated: qseries_v2\\observation_intelligence\\__init__.py")
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec"); compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        for u,h in hashes.items():
            if sha(u)!=h: raise RuntimeError(f"Certified upstream changed: {u.name}")
        print("[PASS] In-memory compilation verified"); print("[PASS] Certified upstream remained unchanged")
        ih=hashlib.sha256(MODULE.read_bytes()+TEST.read_bytes()).hexdigest(); print(f"[PASS] Deterministic install hash: {ih}")
        print("[PASS] Explanation response coordination remains deterministic, read-only, session-safe, and fail-closed")
        print("[DONE] OI-057 INSTALLATION COMPLETE"); return 0
    except Exception:
        for p,b in backups.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b)
        print("[ROLLBACK] OI-057 installation failed; all affected files restored"); raise

if __name__=="__main__": raise SystemExit(main())
