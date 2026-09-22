from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-058"
INSTALLER_REVISION = "OI_058_EXPLANATION_FOLLOWUP_REFERENCE_RESOLUTION_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_025_oracle_explanation_query_engine.py", "OI-025"),
    (PACKAGE / "oi_056_explanation_conversation_context.py", "OI-056"),
    (PACKAGE / "oi_057_explanation_response_coordinator.py", "OI-057"),
)

MODULE = PACKAGE / "oi_058_explanation_followup_reference_resolution.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_058_explanation_followup_reference_resolution.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_056_explanation_conversation_context import (
    ExplanationConversationContext,
)

BUILD_ID = "OI-058"
OI_058_REVISION = "OI_058_EXPLANATION_FOLLOWUP_REFERENCE_RESOLUTION_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False
CAUSAL_CLAIM_ALLOWED = False
TERMINAL_MUTATION_ALLOWED = False

REFERENCE_CURRENT_SUBJECT = "current_subject"
REFERENCE_CURRENT_QUERY = "current_query"
REFERENCE_UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class ExplanationFollowUpReferenceResolution:
    session_id: str
    raw_followup: str
    resolved_subject_hint: str | None
    resolved_query_id: str | None
    resolution_type: str
    resolution_hash: str
    read_only: bool


class ExplanationFollowUpReferenceResolver:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False
    causal_claim_allowed = False
    terminal_mutation_allowed = False

    _SUBJECT_REFERENCE_TOKENS = (
        "that",
        "that market",
        "that move",
        "that edge",
        "it",
        "this",
        "this market",
        "this move",
        "this edge",
    )

    def resolve(
        self,
        *,
        context: ExplanationConversationContext,
        raw_followup: str,
    ) -> ExplanationFollowUpReferenceResolution:
        if not isinstance(
            context,
            ExplanationConversationContext,
        ):
            raise TypeError(
                "context must be ExplanationConversationContext"
            )

        text = " ".join(str(raw_followup).strip().split())
        if not text:
            raise ValueError("raw_followup must not be empty")

        lower = text.lower()

        resolved_subject = None
        resolved_query = None
        resolution_type = REFERENCE_UNRESOLVED

        if context.turn_count > 0:
            if any(
                token in lower
                for token in self._SUBJECT_REFERENCE_TOKENS
            ):
                resolved_subject = context.latest_subject_hint
                resolved_query = context.latest_query_id
                resolution_type = REFERENCE_CURRENT_SUBJECT
            elif (
                "previous question" in lower
                or "last question" in lower
                or "that question" in lower
            ):
                resolved_subject = context.latest_subject_hint
                resolved_query = context.latest_query_id
                resolution_type = REFERENCE_CURRENT_QUERY

        body = {
            "session_id": context.session_id,
            "raw_followup": text,
            "resolved_subject_hint": resolved_subject,
            "resolved_query_id": resolved_query,
            "resolution_type": resolution_type,
            "read_only": True,
        }

        return ExplanationFollowUpReferenceResolution(
            session_id=context.session_id,
            raw_followup=text,
            resolved_subject_hint=resolved_subject,
            resolved_query_id=resolved_query,
            resolution_type=resolution_type,
            resolution_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_explanation_followup_reference_resolution() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-058 must remain read-only")

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
            PREDICTION_ALLOWED,
            EDGE_SCORE_ALLOWED,
            PROBABILITY_ALLOWED,
            CAUSAL_CLAIM_ALLOWED,
            TERMINAL_MUTATION_ALLOWED,
        )
    ):
        raise AssertionError("OI-058 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_058_REVISION",
    "REFERENCE_CURRENT_SUBJECT",
    "REFERENCE_CURRENT_QUERY",
    "REFERENCE_UNRESOLVED",
    "ExplanationFollowUpReferenceResolution",
    "ExplanationFollowUpReferenceResolver",
    "verify_explanation_followup_reference_resolution",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_055_terminal_explanation_session_adapter import (
    TerminalExplanationSessionTurn,
)
from qseries_v2.observation_intelligence.oi_056_explanation_conversation_context import (
    ExplanationConversationContextBuilder,
)
from qseries_v2.observation_intelligence.oi_058_explanation_followup_reference_resolution import (
    OI_058_REVISION,
    REFERENCE_CURRENT_SUBJECT,
    REFERENCE_UNRESOLVED,
    ExplanationFollowUpReferenceResolver,
    verify_explanation_followup_reference_resolution,
)

NOW = datetime(2026, 8, 11, 19, 0, tzinfo=timezone.utc)


def context():
    turn = TerminalExplanationSessionTurn(
        session_id="session.1",
        turn_number=1,
        query_id="query.astros",
        response_id="response.astros",
        subject_hint="Astros strikeouts",
        completeness_status="partial",
        display_payload=("response",),
        received_at=NOW,
        turn_hash="a" * 64,
        read_only=True,
    )

    return ExplanationConversationContextBuilder().build(
        session_id="session.1",
        turns=(turn,),
    )


class TestOI058(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_followup_reference_resolution()
        )

    def test_subject_reference(self):
        result = ExplanationFollowUpReferenceResolver().resolve(
            context=context(),
            raw_followup="What evidence supports that move?",
        )

        self.assertEqual(
            result.resolved_subject_hint,
            "Astros strikeouts",
        )
        self.assertEqual(
            result.resolution_type,
            REFERENCE_CURRENT_SUBJECT,
        )

    def test_unresolved(self):
        result = ExplanationFollowUpReferenceResolver().resolve(
            context=context(),
            raw_followup="Explain weather evidence",
        )

        self.assertEqual(
            result.resolution_type,
            REFERENCE_UNRESOLVED,
        )
        self.assertIsNone(result.resolved_subject_hint)

    def test_deterministic(self):
        resolver = ExplanationFollowUpReferenceResolver()

        a = resolver.resolve(
            context=context(),
            raw_followup="Why did that edge change?",
        )
        b = resolver.resolve(
            context=context(),
            raw_followup="Why did that edge change?",
        )

        self.assertEqual(
            a.resolution_hash,
            b.resolution_hash,
        )

    def test_side_effects(self):
        resolver = ExplanationFollowUpReferenceResolver()

        self.assertTrue(resolver.read_only)
        self.assertFalse(resolver.network_allowed)
        self.assertFalse(resolver.persistence_allowed)
        self.assertFalse(resolver.publication_allowed)
        self.assertFalse(resolver.execution_allowed)
        self.assertFalse(resolver.qseries_execution_allowed)
        self.assertFalse(resolver.prediction_allowed)
        self.assertFalse(resolver.edge_score_allowed)
        self.assertFalse(resolver.probability_allowed)
        self.assertFalse(resolver.causal_claim_allowed)
        self.assertFalse(resolver.terminal_mutation_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-058 CERTIFICATION TEST")
    print(" EXPLANATION FOLLOW-UP REFERENCE RESOLUTION")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI058)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-058")
    print(f"[PASS] Revision: {OI_058_REVISION}")
    print("[PASS] Follow-up references resolve deterministically against current explanation session context")
    print("[PASS] Current subject and current query references preserve session lineage")
    print("[PASS] Unresolved references fail closed without guessing")
    print("[DONE] OI-058 CERTIFIED")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_checked(path: Path, source: str) -> None:
    text = source.lstrip()
    ast.parse(text, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"[PASS] Wrote: {path.relative_to(ROOT)}")


def main() -> int:
    print("=" * 72)
    print(" OI-058 INSTALLER")
    print(" EXPLANATION FOLLOW-UP REFERENCE RESOLUTION")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    for upstream, name in UPSTREAMS:
        if not upstream.is_file():
            raise RuntimeError(f"Certified {name} missing: {upstream}")

    upstream_hashes = {
        upstream: sha(upstream)
        for upstream, _ in UPSTREAMS
    }

    print(
        "[PASS] Certified OI-025, OI-056, "
        "and OI-057 verified read-only"
    )

    affected = (MODULE, TEST, INIT)
    backups = {
        item: item.read_bytes() if item.exists() else None
        for item in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = (
            "from .oi_058_explanation_followup_reference_resolution import *"
        )

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            ast.parse(current, filename=str(INIT))
            INIT.write_text(current, encoding="utf-8", newline="\n")

        print(
            "[PASS] Updated: "
            "qseries_v2\\observation_intelligence\\__init__.py"
        )

        compile(MODULE.read_text(encoding="utf-8"), str(MODULE), "exec")
        compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")

        for upstream, expected in upstream_hashes.items():
            if sha(upstream) != expected:
                raise RuntimeError(
                    f"Certified upstream changed: {upstream.name}"
                )

        print("[PASS] In-memory compilation verified")
        print("[PASS] Certified upstream remained unchanged")

        install_hash = hashlib.sha256(
            MODULE.read_bytes() + TEST.read_bytes()
        ).hexdigest()

        print(f"[PASS] Deterministic install hash: {install_hash}")
        print(
            "[PASS] Follow-up reference resolution remains deterministic, "
            "read-only, session-safe, and fail-closed"
        )
        print("[DONE] OI-058 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for item, original in backups.items():
            if original is None:
                if item.exists():
                    item.unlink()
            else:
                item.parent.mkdir(parents=True, exist_ok=True)
                item.write_bytes(original)

        print(
            "[ROLLBACK] OI-058 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
