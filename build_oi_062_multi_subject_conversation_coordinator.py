from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-062"
INSTALLER_REVISION = "OI_062_MULTI_SUBJECT_CONVERSATION_COORDINATOR_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_056_explanation_conversation_context.py", "OI-056"),
    (PACKAGE / "oi_061_explanation_intent_continuation_classifier.py", "OI-061"),
)

MODULE = PACKAGE / "oi_062_multi_subject_conversation_coordinator.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_062_multi_subject_conversation_coordinator.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_056_explanation_conversation_context import (
    ExplanationConversationContext,
)

BUILD_ID = "OI-062"
OI_062_REVISION = "OI_062_MULTI_SUBJECT_CONVERSATION_COORDINATOR_V1"

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


@dataclass(frozen=True, slots=True)
class MultiSubjectConversationState:
    session_id: str
    active_subject_hint: str | None
    subject_hints: tuple[str, ...]
    subject_turn_counts: tuple[tuple[str, int], ...]
    state_hash: str
    read_only: bool


class MultiSubjectConversationCoordinator:
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
        context: ExplanationConversationContext,
    ) -> MultiSubjectConversationState:
        if not isinstance(
            context,
            ExplanationConversationContext,
        ):
            raise TypeError(
                "context must be ExplanationConversationContext"
            )

        counts = {}

        for turn in context.turns:
            subject = turn.subject_hint
            counts[subject] = counts.get(subject, 0) + 1

        subjects = tuple(sorted(counts))

        subject_turn_counts = tuple(
            (subject, counts[subject])
            for subject in subjects
        )

        body = {
            "session_id": context.session_id,
            "active_subject_hint": (
                context.latest_subject_hint
            ),
            "subject_hints": subjects,
            "subject_turn_counts": subject_turn_counts,
            "read_only": True,
        }

        return MultiSubjectConversationState(
            session_id=context.session_id,
            active_subject_hint=(
                context.latest_subject_hint
            ),
            subject_hints=subjects,
            subject_turn_counts=subject_turn_counts,
            state_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_multi_subject_conversation_coordinator() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-062 must remain read-only")

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
        raise AssertionError(
            "OI-062 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_062_REVISION",
    "MultiSubjectConversationState",
    "MultiSubjectConversationCoordinator",
    "verify_multi_subject_conversation_coordinator",
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
from qseries_v2.observation_intelligence.oi_062_multi_subject_conversation_coordinator import (
    OI_062_REVISION,
    MultiSubjectConversationCoordinator,
    verify_multi_subject_conversation_coordinator,
)

NOW = datetime(2026, 8, 11, 22, 0, tzinfo=timezone.utc)


def turn(number, subject):
    return TerminalExplanationSessionTurn(
        session_id="session.1",
        turn_number=number,
        query_id=f"query.{number}",
        response_id=f"response.{number}",
        subject_hint=subject,
        completeness_status="complete",
        display_payload=(subject,),
        received_at=NOW,
        turn_hash=str(number) * 64,
        read_only=True,
    )


def context():
    return ExplanationConversationContextBuilder().build(
        session_id="session.1",
        turns=(
            turn(1, "Bitcoin"),
            turn(2, "Astros strikeouts"),
            turn(3, "Bitcoin"),
        ),
    )


class TestOI062(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_multi_subject_conversation_coordinator()
        )

    def test_subjects(self):
        state = MultiSubjectConversationCoordinator().coordinate(
            context()
        )

        self.assertEqual(
            state.subject_hints,
            (
                "Astros strikeouts",
                "Bitcoin",
            ),
        )

    def test_active_subject(self):
        state = MultiSubjectConversationCoordinator().coordinate(
            context()
        )

        self.assertEqual(
            state.active_subject_hint,
            "Bitcoin",
        )

    def test_turn_counts(self):
        state = MultiSubjectConversationCoordinator().coordinate(
            context()
        )

        self.assertIn(
            ("Bitcoin", 2),
            state.subject_turn_counts,
        )

        self.assertIn(
            ("Astros strikeouts", 1),
            state.subject_turn_counts,
        )

    def test_deterministic(self):
        coordinator = MultiSubjectConversationCoordinator()

        a = coordinator.coordinate(context())
        b = coordinator.coordinate(context())

        self.assertEqual(
            a.state_hash,
            b.state_hash,
        )

    def test_side_effects(self):
        item = MultiSubjectConversationCoordinator()

        self.assertTrue(item.read_only)
        self.assertFalse(item.network_allowed)
        self.assertFalse(item.persistence_allowed)
        self.assertFalse(item.publication_allowed)
        self.assertFalse(item.execution_allowed)
        self.assertFalse(item.qseries_execution_allowed)
        self.assertFalse(item.prediction_allowed)
        self.assertFalse(item.edge_score_allowed)
        self.assertFalse(item.probability_allowed)
        self.assertFalse(item.causal_claim_allowed)
        self.assertFalse(item.terminal_mutation_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-062 CERTIFICATION TEST")
    print(" MULTI-SUBJECT CONVERSATION COORDINATOR")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI062)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-062")
    print(f"[PASS] Revision: {OI_062_REVISION}")
    print("[PASS] Multiple explanation subjects coordinated within one deterministic session")
    print("[PASS] Active subject, known subjects, and per-subject turn counts certified")
    print("[PASS] Multi-subject state remains read-only, non-mutating, and non-predictive")
    print("[DONE] OI-062 CERTIFIED")
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
    print(" OI-062 INSTALLER")
    print(" MULTI-SUBJECT CONVERSATION COORDINATOR")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    for upstream, name in UPSTREAMS:
        if not upstream.is_file():
            raise RuntimeError(
                f"Certified {name} missing: {upstream}"
            )

    upstream_hashes = {
        upstream: sha(upstream)
        for upstream, _ in UPSTREAMS
    }

    print(
        "[PASS] Certified OI-056 and OI-061 "
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

        current = INIT.read_text(
            encoding="utf-8"
        ) if INIT.exists() else ""

        export = (
            "from .oi_062_multi_subject_conversation_coordinator import *"
        )

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"

            current += export + "\n"
            ast.parse(current, filename=str(INIT))
            INIT.write_text(
                current,
                encoding="utf-8",
                newline="\n",
            )

        print(
            "[PASS] Updated: "
            "qseries_v2\\observation_intelligence\\__init__.py"
        )

        compile(
            MODULE.read_text(encoding="utf-8"),
            str(MODULE),
            "exec",
        )
        compile(
            TEST.read_text(encoding="utf-8"),
            str(TEST),
            "exec",
        )

        for upstream, expected in upstream_hashes.items():
            if sha(upstream) != expected:
                raise RuntimeError(
                    f"Certified upstream changed: "
                    f"{upstream.name}"
                )

        print("[PASS] In-memory compilation verified")
        print("[PASS] Certified upstream remained unchanged")

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + TEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: "
            f"{install_hash}"
        )
        print(
            "[PASS] Multi-subject coordination remains "
            "deterministic, read-only, and fail-closed"
        )
        print("[DONE] OI-062 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for item, original in backups.items():
            if original is None:
                if item.exists():
                    item.unlink()
            else:
                item.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )
                item.write_bytes(original)

        print(
            "[ROLLBACK] OI-062 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
