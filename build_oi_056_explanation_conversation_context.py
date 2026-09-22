from __future__ import annotations
import ast, hashlib
from pathlib import Path

BUILD_ID="OI-056"
INSTALLER_REVISION="OI_056_EXPLANATION_CONVERSATION_CONTEXT_INSTALLER_V1"
ROOT=Path.cwd().resolve()
PACKAGE=ROOT/"qseries_v2"/"observation_intelligence"
UPSTREAMS=((PACKAGE/"oi_055_terminal_explanation_session_adapter.py","OI-055"),)
MODULE=PACKAGE/"oi_056_explanation_conversation_context.py"
INIT=PACKAGE/"__init__.py"
TEST=ROOT/"test_oi_056_explanation_conversation_context.py"

MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_055_terminal_explanation_session_adapter import TerminalExplanationSessionTurn

BUILD_ID="OI-056"
OI_056_REVISION="OI_056_EXPLANATION_CONVERSATION_CONTEXT_V1"
READ_ONLY=True
NETWORK_ALLOWED=PERSISTENCE_ALLOWED=PUBLICATION_ALLOWED=False
EXECUTION_ALLOWED=QSERIES_EXECUTION_ALLOWED=False
PREDICTION_ALLOWED=EDGE_SCORE_ALLOWED=PROBABILITY_ALLOWED=False
CAUSAL_CLAIM_ALLOWED=TERMINAL_MUTATION_ALLOWED=False

@dataclass(frozen=True, slots=True)
class ExplanationConversationContext:
    session_id:str
    turns:tuple[TerminalExplanationSessionTurn,...]
    turn_count:int
    latest_query_id:str|None
    latest_subject_hint:str|None
    latest_completeness_status:str|None
    context_hash:str
    read_only:bool

class ExplanationConversationContextBuilder:
    read_only=True
    network_allowed=persistence_allowed=publication_allowed=False
    execution_allowed=qseries_execution_allowed=False
    prediction_allowed=edge_score_allowed=probability_allowed=False
    causal_claim_allowed=terminal_mutation_allowed=False

    def build(self,*,session_id:str,turns:tuple[TerminalExplanationSessionTurn,...])->ExplanationConversationContext:
        sid=str(session_id).strip()
        if not sid: raise ValueError("session_id must not be empty")
        values=tuple(turns)
        if any(not isinstance(x,TerminalExplanationSessionTurn) for x in values):
            raise TypeError("all turns must be TerminalExplanationSessionTurn")
        if any(x.session_id!=sid for x in values):
            raise ValueError("all turns must belong to the requested session_id")
        if values!=tuple(sorted(values,key=lambda x:x.turn_number)):
            raise ValueError("turns must be supplied in deterministic turn order")
        nums=tuple(x.turn_number for x in values)
        if len(nums)!=len(set(nums)): raise ValueError("duplicate turn_number in conversation context")
        latest=values[-1] if values else None
        body={
            "session_id":sid,"turn_hashes":tuple(x.turn_hash for x in values),
            "turn_count":len(values),
            "latest_query_id":latest.query_id if latest else None,
            "latest_subject_hint":latest.subject_hint if latest else None,
            "latest_completeness_status":latest.completeness_status if latest else None,
            "read_only":True,
        }
        return ExplanationConversationContext(
            session_id=sid,turns=values,turn_count=len(values),
            latest_query_id=latest.query_id if latest else None,
            latest_subject_hint=latest.subject_hint if latest else None,
            latest_completeness_status=latest.completeness_status if latest else None,
            context_hash=deterministic_sha256(body),read_only=True)

def verify_explanation_conversation_context()->bool:
    if READ_ONLY is not True: raise AssertionError("OI-056 must remain read-only")
    if any((NETWORK_ALLOWED,PERSISTENCE_ALLOWED,PUBLICATION_ALLOWED,EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,PREDICTION_ALLOWED,EDGE_SCORE_ALLOWED,
            PROBABILITY_ALLOWED,CAUSAL_CLAIM_ALLOWED,TERMINAL_MUTATION_ALLOWED)):
        raise AssertionError("OI-056 forbidden capability enabled")
    return True

__all__=["BUILD_ID","OI_056_REVISION","ExplanationConversationContext",
         "ExplanationConversationContextBuilder","verify_explanation_conversation_context"]
"""

TEST_SOURCE=r"""
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
"""

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write_checked(path,source):
    text=source.lstrip(); ast.parse(text,filename=str(path)); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding="utf-8",newline="\n"); print(f"[PASS] Wrote: {path.relative_to(ROOT)}")

def main():
    print("="*72); print(" OI-056 INSTALLER"); print(" EXPLANATION CONVERSATION CONTEXT"); print("="*72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}"); print(f"[ROOT] {ROOT}")
    for u,n in UPSTREAMS:
        if not u.is_file(): raise RuntimeError(f"Certified {n} missing: {u}")
    hashes={u:sha(u) for u,_ in UPSTREAMS}; print("[PASS] Certified OI-055 verified read-only")
    affected=(MODULE,TEST,INIT); backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_checked(MODULE,MODULE_SOURCE); write_checked(TEST,TEST_SOURCE)
        current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .oi_056_explanation_conversation_context import *"
        if export not in current.splitlines():
            if current and not current.endswith("\n"): current+="\n"
            current+=export+"\n"; ast.parse(current,filename=str(INIT)); INIT.write_text(current,encoding="utf-8",newline="\n")
        print("[PASS] Updated: qseries_v2\\observation_intelligence\\__init__.py")
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec"); compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        for u,h in hashes.items():
            if sha(u)!=h: raise RuntimeError(f"Certified upstream changed: {u.name}")
        print("[PASS] In-memory compilation verified"); print("[PASS] Certified upstream remained unchanged")
        ih=hashlib.sha256(MODULE.read_bytes()+TEST.read_bytes()).hexdigest(); print(f"[PASS] Deterministic install hash: {ih}")
        print("[PASS] Explanation conversation context remains deterministic, read-only, ordered, and fail-closed")
        print("[DONE] OI-056 INSTALLATION COMPLETE"); return 0
    except Exception:
        for p,b in backups.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b)
        print("[ROLLBACK] OI-056 installation failed; all affected files restored"); raise

if __name__=="__main__": raise SystemExit(main())
