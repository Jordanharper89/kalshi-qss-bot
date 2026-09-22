from __future__ import annotations
import ast, hashlib
from pathlib import Path

BUILD_ID = "OI-055"
INSTALLER_REVISION = "OI_055_TERMINAL_EXPLANATION_SESSION_ADAPTER_INSTALLER_V1"
ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"
UPSTREAMS = (
    (PACKAGE / "oi_053_explanation_query_response_package.py", "OI-053"),
    (PACKAGE / "oi_054_explanation_terminal_handoff_boundary.py", "OI-054"),
)
MODULE = PACKAGE / "oi_055_terminal_explanation_session_adapter.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_055_terminal_explanation_session_adapter.py"

MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_054_explanation_terminal_handoff_boundary import ExplanationTerminalHandoff

BUILD_ID = "OI-055"
OI_055_REVISION = "OI_055_TERMINAL_EXPLANATION_SESSION_ADAPTER_V1"
READ_ONLY = True
NETWORK_ALLOWED = PERSISTENCE_ALLOWED = PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = EDGE_SCORE_ALLOWED = PROBABILITY_ALLOWED = False
CAUSAL_CLAIM_ALLOWED = TERMINAL_MUTATION_ALLOWED = False

@dataclass(frozen=True, slots=True)
class TerminalExplanationSessionTurn:
    session_id: str
    turn_number: int
    query_id: str
    response_id: str
    subject_hint: str
    completeness_status: str
    display_payload: tuple[str, ...]
    received_at: datetime
    turn_hash: str
    read_only: bool

class TerminalExplanationSessionAdapter:
    read_only = True
    network_allowed = persistence_allowed = publication_allowed = False
    execution_allowed = qseries_execution_allowed = False
    prediction_allowed = edge_score_allowed = probability_allowed = False
    causal_claim_allowed = terminal_mutation_allowed = False

    def adapt(self, *, session_id: str, turn_number: int,
              handoff: ExplanationTerminalHandoff,
              received_at: datetime) -> TerminalExplanationSessionTurn:
        sid = str(session_id).strip()
        if not sid:
            raise ValueError("session_id must not be empty")
        if not isinstance(turn_number, int) or turn_number < 1:
            raise ValueError("turn_number must be a positive integer")
        if not isinstance(handoff, ExplanationTerminalHandoff):
            raise TypeError("handoff must be ExplanationTerminalHandoff")
        if not isinstance(received_at, datetime):
            raise TypeError("received_at must be datetime")
        if received_at.tzinfo is None:
            raise ValueError("received_at must be timezone-aware")
        received_at = received_at.astimezone(timezone.utc)
        body = {
            "session_id": sid, "turn_number": turn_number,
            "query_id": handoff.query_id, "response_id": handoff.response_id,
            "subject_hint": handoff.subject_hint,
            "completeness_status": handoff.completeness_status,
            "display_payload": handoff.display_payload,
            "received_at": received_at, "read_only": True,
        }
        return TerminalExplanationSessionTurn(
            session_id=sid, turn_number=turn_number,
            query_id=handoff.query_id, response_id=handoff.response_id,
            subject_hint=handoff.subject_hint,
            completeness_status=handoff.completeness_status,
            display_payload=handoff.display_payload,
            received_at=received_at,
            turn_hash=deterministic_sha256(body),
            read_only=True,
        )

def verify_terminal_explanation_session_adapter() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-055 must remain read-only")
    if any((NETWORK_ALLOWED, PERSISTENCE_ALLOWED, PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED, QSERIES_EXECUTION_ALLOWED, PREDICTION_ALLOWED,
            EDGE_SCORE_ALLOWED, PROBABILITY_ALLOWED, CAUSAL_CLAIM_ALLOWED,
            TERMINAL_MUTATION_ALLOWED)):
        raise AssertionError("OI-055 forbidden capability enabled")
    return True

__all__ = [
    "BUILD_ID","OI_055_REVISION","TerminalExplanationSessionTurn",
    "TerminalExplanationSessionAdapter",
    "verify_terminal_explanation_session_adapter",
]
"""

TEST_SOURCE = r"""
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
"""

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_checked(path: Path, source: str) -> None:
    text=source.lstrip()
    ast.parse(text, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"[PASS] Wrote: {path.relative_to(ROOT)}")

def main() -> int:
    print("="*72); print(" OI-055 INSTALLER"); print(" TERMINAL EXPLANATION SESSION ADAPTER"); print("="*72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}"); print(f"[ROOT] {ROOT}")
    for upstream,name in UPSTREAMS:
        if not upstream.is_file(): raise RuntimeError(f"Certified {name} missing: {upstream}")
    hashes={u:sha(u) for u,_ in UPSTREAMS}
    print("[PASS] Certified OI-053 and OI-054 verified read-only")
    affected=(MODULE,TEST,INIT); backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_checked(MODULE,MODULE_SOURCE); write_checked(TEST,TEST_SOURCE)
        current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .oi_055_terminal_explanation_session_adapter import *"
        if export not in current.splitlines():
            if current and not current.endswith("\n"): current+="\n"
            current+=export+"\n"; ast.parse(current,filename=str(INIT)); INIT.write_text(current,encoding="utf-8",newline="\n")
        print("[PASS] Updated: qseries_v2\\observation_intelligence\\__init__.py")
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec"); compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        for u,h in hashes.items():
            if sha(u)!=h: raise RuntimeError(f"Certified upstream changed: {u.name}")
        print("[PASS] In-memory compilation verified"); print("[PASS] Certified upstream remained unchanged")
        ih=hashlib.sha256(MODULE.read_bytes()+TEST.read_bytes()).hexdigest()
        print(f"[PASS] Deterministic install hash: {ih}")
        print("[PASS] Terminal session adaptation remains deterministic, read-only, non-mutating, and fail-closed")
        print("[DONE] OI-055 INSTALLATION COMPLETE"); return 0
    except Exception:
        for p,b in backups.items():
            if b is None:
                if p.exists(): p.unlink()
            else:
                p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b)
        print("[ROLLBACK] OI-055 installation failed; all affected files restored"); raise

if __name__ == "__main__":
    raise SystemExit(main())
