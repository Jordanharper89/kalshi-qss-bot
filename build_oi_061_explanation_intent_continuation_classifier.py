from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-061"
INSTALLER_REVISION = "OI_061_EXPLANATION_INTENT_CONTINUATION_CLASSIFIER_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_025_oracle_explanation_query_engine.py", "OI-025"),
    (PACKAGE / "oi_058_explanation_followup_reference_resolution.py", "OI-058"),
    (PACKAGE / "oi_060_explanation_continuation_coordinator.py", "OI-060"),
)

MODULE = PACKAGE / "oi_061_explanation_intent_continuation_classifier.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_061_explanation_intent_continuation_classifier.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_058_explanation_followup_reference_resolution import (
    ExplanationFollowUpReferenceResolution,
)
from .oi_060_explanation_continuation_coordinator import (
    OracleExplanationContinuation,
)

BUILD_ID = "OI-061"
OI_061_REVISION = "OI_061_EXPLANATION_INTENT_CONTINUATION_CLASSIFIER_V1"

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

INTENT_CONTINUE = "continue_explanation"
INTENT_MORE_EVIDENCE = "more_evidence"
INTENT_CONTRADICTION = "contradiction"
INTENT_TIMELINE = "timeline"
INTENT_NEW_SUBJECT = "new_subject"
INTENT_UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class ExplanationContinuationIntent:
    session_id: str
    raw_followup: str
    intent: str
    resolved_subject_hint: str | None
    resolved_query_id: str | None
    intent_hash: str
    read_only: bool


class ExplanationIntentContinuationClassifier:
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

    def classify(
        self,
        *,
        reference: ExplanationFollowUpReferenceResolution,
        continuation: OracleExplanationContinuation,
    ) -> ExplanationContinuationIntent:
        if not isinstance(
            reference,
            ExplanationFollowUpReferenceResolution,
        ):
            raise TypeError(
                "reference must be ExplanationFollowUpReferenceResolution"
            )

        if not isinstance(
            continuation,
            OracleExplanationContinuation,
        ):
            raise TypeError(
                "continuation must be OracleExplanationContinuation"
            )

        if reference.session_id != continuation.session_id:
            raise ValueError(
                "reference/continuation session_id mismatch"
            )

        text = reference.raw_followup.lower()

        if continuation.continuation_status == "continue_unresolved":
            intent = INTENT_UNRESOLVED
        elif any(
            token in text
            for token in (
                "contradict",
                "contradiction",
                "conflict",
                "disagree",
            )
        ):
            intent = INTENT_CONTRADICTION
        elif any(
            token in text
            for token in (
                "timeline",
                "when did",
                "what changed",
                "since",
            )
        ):
            intent = INTENT_TIMELINE
        elif any(
            token in text
            for token in (
                "evidence",
                "support",
                "sources",
                "show me more",
            )
        ):
            intent = INTENT_MORE_EVIDENCE
        elif any(
            token in text
            for token in (
                "another market",
                "different market",
                "different subject",
                "new subject",
            )
        ):
            intent = INTENT_NEW_SUBJECT
        else:
            intent = INTENT_CONTINUE

        body = {
            "session_id": reference.session_id,
            "raw_followup": reference.raw_followup,
            "intent": intent,
            "resolved_subject_hint": (
                reference.resolved_subject_hint
            ),
            "resolved_query_id": (
                reference.resolved_query_id
            ),
            "read_only": True,
        }

        return ExplanationContinuationIntent(
            session_id=reference.session_id,
            raw_followup=reference.raw_followup,
            intent=intent,
            resolved_subject_hint=(
                reference.resolved_subject_hint
            ),
            resolved_query_id=(
                reference.resolved_query_id
            ),
            intent_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_explanation_intent_continuation_classifier() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-061 must remain read-only")

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
            "OI-061 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_061_REVISION",
    "INTENT_CONTINUE",
    "INTENT_MORE_EVIDENCE",
    "INTENT_CONTRADICTION",
    "INTENT_TIMELINE",
    "INTENT_NEW_SUBJECT",
    "INTENT_UNRESOLVED",
    "ExplanationContinuationIntent",
    "ExplanationIntentContinuationClassifier",
    "verify_explanation_intent_continuation_classifier",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_058_explanation_followup_reference_resolution import (
    ExplanationFollowUpReferenceResolution,
)
from qseries_v2.observation_intelligence.oi_060_explanation_continuation_coordinator import (
    OracleExplanationContinuation,
)
from qseries_v2.observation_intelligence.oi_061_explanation_intent_continuation_classifier import (
    OI_061_REVISION,
    INTENT_CONTRADICTION,
    INTENT_MORE_EVIDENCE,
    INTENT_TIMELINE,
    INTENT_UNRESOLVED,
    ExplanationIntentContinuationClassifier,
    verify_explanation_intent_continuation_classifier,
)


def reference(text, resolved=True):
    return ExplanationFollowUpReferenceResolution(
        session_id="session.1",
        raw_followup=text,
        resolved_subject_hint=(
            "Astros strikeouts" if resolved else None
        ),
        resolved_query_id=(
            "query.astros" if resolved else None
        ),
        resolution_type=(
            "current_subject" if resolved else "unresolved"
        ),
        resolution_hash="a" * 64,
        read_only=True,
    )


def continuation(resolved=True):
    return OracleExplanationContinuation(
        session_id="session.1",
        continuation_status=(
            "continue_resolved"
            if resolved
            else "continue_unresolved"
        ),
        resolved_subject_hint=(
            "Astros strikeouts" if resolved else None
        ),
        resolved_query_id=(
            "query.astros" if resolved else None
        ),
        session_change_type="none",
        prior_turn_count=1,
        continuation_hash="b" * 64,
        read_only=True,
    )


class TestOI061(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_intent_continuation_classifier()
        )

    def test_more_evidence(self):
        result = ExplanationIntentContinuationClassifier().classify(
            reference=reference(
                "What evidence supports that move?"
            ),
            continuation=continuation(),
        )

        self.assertEqual(
            result.intent,
            INTENT_MORE_EVIDENCE,
        )

    def test_contradiction(self):
        result = ExplanationIntentContinuationClassifier().classify(
            reference=reference(
                "What evidence contradicts that?"
            ),
            continuation=continuation(),
        )

        self.assertEqual(
            result.intent,
            INTENT_CONTRADICTION,
        )

    def test_timeline(self):
        result = ExplanationIntentContinuationClassifier().classify(
            reference=reference(
                "What changed since the last answer?"
            ),
            continuation=continuation(),
        )

        self.assertEqual(
            result.intent,
            INTENT_TIMELINE,
        )

    def test_unresolved(self):
        result = ExplanationIntentContinuationClassifier().classify(
            reference=reference(
                "Explain something else",
                False,
            ),
            continuation=continuation(False),
        )

        self.assertEqual(
            result.intent,
            INTENT_UNRESOLVED,
        )

    def test_deterministic(self):
        classifier = ExplanationIntentContinuationClassifier()

        a = classifier.classify(
            reference=reference(
                "What evidence supports that move?"
            ),
            continuation=continuation(),
        )
        b = classifier.classify(
            reference=reference(
                "What evidence supports that move?"
            ),
            continuation=continuation(),
        )

        self.assertEqual(
            a.intent_hash,
            b.intent_hash,
        )

    def test_side_effects(self):
        item = ExplanationIntentContinuationClassifier()

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
    print(" OI-061 CERTIFICATION TEST")
    print(" EXPLANATION INTENT CONTINUATION CLASSIFIER")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI061)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-061")
    print(f"[PASS] Revision: {OI_061_REVISION}")
    print("[PASS] Continue, evidence, contradiction, timeline, new-subject, and unresolved intents certified")
    print("[PASS] Follow-up intent classification remains deterministic and session-bound")
    print("[PASS] Unresolved continuation fails closed without guessing")
    print("[DONE] OI-061 CERTIFIED")
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
    print(" OI-061 INSTALLER")
    print(" EXPLANATION INTENT CONTINUATION CLASSIFIER")
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
        "[PASS] Certified OI-025, OI-058, "
        "and OI-060 verified read-only"
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
            "from .oi_061_explanation_intent_continuation_classifier import *"
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
            "[PASS] Intent continuation classification remains "
            "deterministic, read-only, and fail-closed"
        )
        print("[DONE] OI-061 INSTALLATION COMPLETE")
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
            "[ROLLBACK] OI-061 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
