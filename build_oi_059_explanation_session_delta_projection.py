from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-059"
INSTALLER_REVISION = "OI_059_EXPLANATION_SESSION_DELTA_PROJECTION_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_056_explanation_conversation_context.py", "OI-056"),
    (PACKAGE / "oi_058_explanation_followup_reference_resolution.py", "OI-058"),
)

MODULE = PACKAGE / "oi_059_explanation_session_delta_projection.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_059_explanation_session_delta_projection.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_056_explanation_conversation_context import (
    ExplanationConversationContext,
)

BUILD_ID = "OI-059"
OI_059_REVISION = "OI_059_EXPLANATION_SESSION_DELTA_PROJECTION_V1"

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

CHANGE_NONE = "none"
CHANGE_QUERY = "query_changed"
CHANGE_SUBJECT = "subject_changed"
CHANGE_COMPLETENESS = "completeness_changed"
CHANGE_MULTIPLE = "multiple_changes"


@dataclass(frozen=True, slots=True)
class ExplanationSessionDelta:
    session_id: str
    previous_turn_number: int | None
    current_turn_number: int | None
    query_changed: bool
    subject_changed: bool
    completeness_changed: bool
    change_type: str
    delta_hash: str
    read_only: bool


class ExplanationSessionDeltaProjector:
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

    def project(
        self,
        context: ExplanationConversationContext,
    ) -> ExplanationSessionDelta:
        if not isinstance(
            context,
            ExplanationConversationContext,
        ):
            raise TypeError(
                "context must be ExplanationConversationContext"
            )

        previous = (
            context.turns[-2]
            if context.turn_count >= 2
            else None
        )
        current = (
            context.turns[-1]
            if context.turn_count >= 1
            else None
        )

        if previous is None or current is None:
            query_changed = False
            subject_changed = False
            completeness_changed = False
            change_type = CHANGE_NONE
        else:
            query_changed = previous.query_id != current.query_id
            subject_changed = (
                previous.subject_hint != current.subject_hint
            )
            completeness_changed = (
                previous.completeness_status
                != current.completeness_status
            )

            changed_count = sum(
                (
                    query_changed,
                    subject_changed,
                    completeness_changed,
                )
            )

            if changed_count == 0:
                change_type = CHANGE_NONE
            elif changed_count > 1:
                change_type = CHANGE_MULTIPLE
            elif query_changed:
                change_type = CHANGE_QUERY
            elif subject_changed:
                change_type = CHANGE_SUBJECT
            else:
                change_type = CHANGE_COMPLETENESS

        body = {
            "session_id": context.session_id,
            "previous_turn_number": (
                previous.turn_number if previous else None
            ),
            "current_turn_number": (
                current.turn_number if current else None
            ),
            "query_changed": query_changed,
            "subject_changed": subject_changed,
            "completeness_changed": completeness_changed,
            "change_type": change_type,
            "read_only": True,
        }

        return ExplanationSessionDelta(
            session_id=context.session_id,
            previous_turn_number=(
                previous.turn_number if previous else None
            ),
            current_turn_number=(
                current.turn_number if current else None
            ),
            query_changed=query_changed,
            subject_changed=subject_changed,
            completeness_changed=completeness_changed,
            change_type=change_type,
            delta_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_explanation_session_delta_projection() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-059 must remain read-only")

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
        raise AssertionError("OI-059 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_059_REVISION",
    "CHANGE_NONE",
    "CHANGE_QUERY",
    "CHANGE_SUBJECT",
    "CHANGE_COMPLETENESS",
    "CHANGE_MULTIPLE",
    "ExplanationSessionDelta",
    "ExplanationSessionDeltaProjector",
    "verify_explanation_session_delta_projection",
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
from qseries_v2.observation_intelligence.oi_059_explanation_session_delta_projection import (
    OI_059_REVISION,
    CHANGE_COMPLETENESS,
    CHANGE_MULTIPLE,
    CHANGE_NONE,
    ExplanationSessionDeltaProjector,
    verify_explanation_session_delta_projection,
)

NOW = datetime(2026, 8, 11, 20, 0, tzinfo=timezone.utc)


def turn(number, query_id, subject, status):
    return TerminalExplanationSessionTurn(
        session_id="session.1",
        turn_number=number,
        query_id=query_id,
        response_id=f"response.{number}",
        subject_hint=subject,
        completeness_status=status,
        display_payload=(f"turn {number}",),
        received_at=NOW,
        turn_hash=str(number) * 64,
        read_only=True,
    )


def context(turns):
    return ExplanationConversationContextBuilder().build(
        session_id="session.1",
        turns=tuple(turns),
    )


class TestOI059(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_session_delta_projection()
        )

    def test_no_delta_first_turn(self):
        result = ExplanationSessionDeltaProjector().project(
            context(
                (
                    turn(
                        1,
                        "query.1",
                        "Astros strikeouts",
                        "partial",
                    ),
                )
            )
        )

        self.assertEqual(result.change_type, CHANGE_NONE)

    def test_completeness_delta(self):
        result = ExplanationSessionDeltaProjector().project(
            context(
                (
                    turn(
                        1,
                        "query.1",
                        "Astros strikeouts",
                        "partial",
                    ),
                    turn(
                        2,
                        "query.1",
                        "Astros strikeouts",
                        "complete",
                    ),
                )
            )
        )

        self.assertEqual(
            result.change_type,
            CHANGE_COMPLETENESS,
        )

    def test_multiple_delta(self):
        result = ExplanationSessionDeltaProjector().project(
            context(
                (
                    turn(
                        1,
                        "query.1",
                        "Astros strikeouts",
                        "partial",
                    ),
                    turn(
                        2,
                        "query.2",
                        "Bitcoin",
                        "complete",
                    ),
                )
            )
        )

        self.assertEqual(
            result.change_type,
            CHANGE_MULTIPLE,
        )

    def test_deterministic(self):
        projector = ExplanationSessionDeltaProjector()
        value = context(
            (
                turn(
                    1,
                    "query.1",
                    "Astros strikeouts",
                    "partial",
                ),
                turn(
                    2,
                    "query.1",
                    "Astros strikeouts",
                    "complete",
                ),
            )
        )

        a = projector.project(value)
        b = projector.project(value)

        self.assertEqual(
            a.delta_hash,
            b.delta_hash,
        )

    def test_side_effects(self):
        projector = ExplanationSessionDeltaProjector()

        self.assertTrue(projector.read_only)
        self.assertFalse(projector.network_allowed)
        self.assertFalse(projector.persistence_allowed)
        self.assertFalse(projector.publication_allowed)
        self.assertFalse(projector.execution_allowed)
        self.assertFalse(projector.qseries_execution_allowed)
        self.assertFalse(projector.prediction_allowed)
        self.assertFalse(projector.edge_score_allowed)
        self.assertFalse(projector.probability_allowed)
        self.assertFalse(projector.causal_claim_allowed)
        self.assertFalse(projector.terminal_mutation_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-059 CERTIFICATION TEST")
    print(" EXPLANATION SESSION DELTA PROJECTION")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI059)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-059")
    print(f"[PASS] Revision: {OI_059_REVISION}")
    print("[PASS] Query, subject, and completeness changes projected across explanation session turns")
    print("[PASS] First-turn, no-change, single-change, and multiple-change states remain deterministic")
    print("[PASS] Session delta projection introduces no causal claim, prediction, probability, or score")
    print("[DONE] OI-059 CERTIFIED")
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
    print(" OI-059 INSTALLER")
    print(" EXPLANATION SESSION DELTA PROJECTION")
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
        "[PASS] Certified OI-056 and OI-058 "
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
        export = "from .oi_059_explanation_session_delta_projection import *"

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
            "[PASS] Explanation session delta projection remains deterministic, "
            "read-only, non-mutating, and fail-closed"
        )
        print("[DONE] OI-059 INSTALLATION COMPLETE")
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
            "[ROLLBACK] OI-059 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
