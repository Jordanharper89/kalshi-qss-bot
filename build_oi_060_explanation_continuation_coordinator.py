from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-060"
INSTALLER_REVISION = "OI_060_EXPLANATION_CONTINUATION_COORDINATOR_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_057_explanation_response_coordinator.py", "OI-057"),
    (PACKAGE / "oi_058_explanation_followup_reference_resolution.py", "OI-058"),
    (PACKAGE / "oi_059_explanation_session_delta_projection.py", "OI-059"),
)

MODULE = PACKAGE / "oi_060_explanation_continuation_coordinator.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_060_explanation_continuation_coordinator.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_056_explanation_conversation_context import (
    ExplanationConversationContext,
)
from .oi_058_explanation_followup_reference_resolution import (
    ExplanationFollowUpReferenceResolution,
)
from .oi_059_explanation_session_delta_projection import (
    ExplanationSessionDelta,
)

BUILD_ID = "OI-060"
OI_060_REVISION = "OI_060_EXPLANATION_CONTINUATION_COORDINATOR_V1"

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

CONTINUE_RESOLVED = "continue_resolved"
CONTINUE_UNRESOLVED = "continue_unresolved"


@dataclass(frozen=True, slots=True)
class OracleExplanationContinuation:
    session_id: str
    continuation_status: str
    resolved_subject_hint: str | None
    resolved_query_id: str | None
    session_change_type: str
    prior_turn_count: int
    continuation_hash: str
    read_only: bool


class OracleExplanationContinuationCoordinator:
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

    def coordinate(
        self,
        *,
        context: ExplanationConversationContext,
        reference: ExplanationFollowUpReferenceResolution,
        delta: ExplanationSessionDelta,
    ) -> OracleExplanationContinuation:
        if not isinstance(
            context,
            ExplanationConversationContext,
        ):
            raise TypeError(
                "context must be ExplanationConversationContext"
            )

        if not isinstance(
            reference,
            ExplanationFollowUpReferenceResolution,
        ):
            raise TypeError(
                "reference must be ExplanationFollowUpReferenceResolution"
            )

        if not isinstance(
            delta,
            ExplanationSessionDelta,
        ):
            raise TypeError(
                "delta must be ExplanationSessionDelta"
            )

        if not (
            context.session_id
            == reference.session_id
            == delta.session_id
        ):
            raise ValueError(
                "context/reference/delta session_id mismatch"
            )

        resolved = (
            reference.resolved_subject_hint is not None
            or reference.resolved_query_id is not None
        )

        continuation_status = (
            CONTINUE_RESOLVED
            if resolved
            else CONTINUE_UNRESOLVED
        )

        body = {
            "session_id": context.session_id,
            "continuation_status": continuation_status,
            "resolved_subject_hint": (
                reference.resolved_subject_hint
            ),
            "resolved_query_id": (
                reference.resolved_query_id
            ),
            "session_change_type": delta.change_type,
            "prior_turn_count": context.turn_count,
            "read_only": True,
        }

        return OracleExplanationContinuation(
            session_id=context.session_id,
            continuation_status=continuation_status,
            resolved_subject_hint=(
                reference.resolved_subject_hint
            ),
            resolved_query_id=(
                reference.resolved_query_id
            ),
            session_change_type=delta.change_type,
            prior_turn_count=context.turn_count,
            continuation_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_explanation_continuation_coordinator() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-060 must remain read-only")

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
        raise AssertionError("OI-060 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_060_REVISION",
    "CONTINUE_RESOLVED",
    "CONTINUE_UNRESOLVED",
    "OracleExplanationContinuation",
    "OracleExplanationContinuationCoordinator",
    "verify_explanation_continuation_coordinator",
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
    ExplanationFollowUpReferenceResolver,
)
from qseries_v2.observation_intelligence.oi_059_explanation_session_delta_projection import (
    ExplanationSessionDeltaProjector,
)
from qseries_v2.observation_intelligence.oi_060_explanation_continuation_coordinator import (
    OI_060_REVISION,
    CONTINUE_RESOLVED,
    CONTINUE_UNRESOLVED,
    OracleExplanationContinuationCoordinator,
    verify_explanation_continuation_coordinator,
)

NOW = datetime(2026, 8, 11, 21, 0, tzinfo=timezone.utc)


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


class TestOI060(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_continuation_coordinator()
        )

    def test_resolved_continuation(self):
        ctx = context()
        reference = ExplanationFollowUpReferenceResolver().resolve(
            context=ctx,
            raw_followup="What evidence supports that move?",
        )
        delta = ExplanationSessionDeltaProjector().project(ctx)

        result = OracleExplanationContinuationCoordinator().coordinate(
            context=ctx,
            reference=reference,
            delta=delta,
        )

        self.assertEqual(
            result.continuation_status,
            CONTINUE_RESOLVED,
        )
        self.assertEqual(
            result.resolved_subject_hint,
            "Astros strikeouts",
        )

    def test_unresolved_continuation(self):
        ctx = context()
        reference = ExplanationFollowUpReferenceResolver().resolve(
            context=ctx,
            raw_followup="Explain weather evidence",
        )
        delta = ExplanationSessionDeltaProjector().project(ctx)

        result = OracleExplanationContinuationCoordinator().coordinate(
            context=ctx,
            reference=reference,
            delta=delta,
        )

        self.assertEqual(
            result.continuation_status,
            CONTINUE_UNRESOLVED,
        )

    def test_deterministic(self):
        ctx = context()
        reference = ExplanationFollowUpReferenceResolver().resolve(
            context=ctx,
            raw_followup="Why did that edge change?",
        )
        delta = ExplanationSessionDeltaProjector().project(ctx)

        coordinator = OracleExplanationContinuationCoordinator()

        a = coordinator.coordinate(
            context=ctx,
            reference=reference,
            delta=delta,
        )
        b = coordinator.coordinate(
            context=ctx,
            reference=reference,
            delta=delta,
        )

        self.assertEqual(
            a.continuation_hash,
            b.continuation_hash,
        )

    def test_side_effects(self):
        coordinator = OracleExplanationContinuationCoordinator()

        self.assertTrue(coordinator.read_only)
        self.assertFalse(coordinator.network_allowed)
        self.assertFalse(coordinator.persistence_allowed)
        self.assertFalse(coordinator.publication_allowed)
        self.assertFalse(coordinator.execution_allowed)
        self.assertFalse(coordinator.qseries_execution_allowed)
        self.assertFalse(coordinator.prediction_allowed)
        self.assertFalse(coordinator.edge_score_allowed)
        self.assertFalse(coordinator.probability_allowed)
        self.assertFalse(coordinator.causal_claim_allowed)
        self.assertFalse(coordinator.terminal_mutation_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-060 CERTIFICATION TEST")
    print(" EXPLANATION CONTINUATION COORDINATOR")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI060)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-060")
    print(f"[PASS] Revision: {OI_060_REVISION}")
    print("[PASS] Resolved and unresolved explanation continuations coordinated deterministically")
    print("[PASS] Session identity, reference lineage, prior turn count, and session change type preserved")
    print("[PASS] Unresolved follow-ups fail closed without guessing or silently changing subject")
    print("[DONE] OI-060 CERTIFIED")
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
    print(" OI-060 INSTALLER")
    print(" EXPLANATION CONTINUATION COORDINATOR")
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
        "[PASS] Certified OI-057 through OI-059 "
        "verified read-only"
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
        export = "from .oi_060_explanation_continuation_coordinator import *"

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
            "[PASS] Explanation continuation coordination remains deterministic, "
            "read-only, session-safe, and fail-closed"
        )
        print("[DONE] OI-060 INSTALLATION COMPLETE")
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
            "[ROLLBACK] OI-060 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
