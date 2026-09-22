from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-064"
INSTALLER_REVISION = "OI_064_FOLLOWUP_EVIDENCE_REQUIREMENT_PROJECTION_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_061_explanation_intent_continuation_classifier.py", "OI-061"),
    (PACKAGE / "oi_063_explanation_context_switch_resolution.py", "OI-063"),
)

MODULE = PACKAGE / "oi_064_followup_evidence_requirement_projection.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_064_followup_evidence_requirement_projection.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_061_explanation_intent_continuation_classifier import (
    ExplanationContinuationIntent,
    INTENT_CONTINUE,
    INTENT_MORE_EVIDENCE,
    INTENT_CONTRADICTION,
    INTENT_TIMELINE,
    INTENT_NEW_SUBJECT,
    INTENT_UNRESOLVED,
)

BUILD_ID = "OI-064"
OI_064_REVISION = "OI_064_FOLLOWUP_EVIDENCE_REQUIREMENT_PROJECTION_V1"

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

NEED_CURRENT_EVIDENCE = "current_evidence"
NEED_ADDITIONAL_EVIDENCE = "additional_evidence"
NEED_CONTRADICTORY_EVIDENCE = "contradictory_evidence"
NEED_TEMPORAL_EVIDENCE = "temporal_evidence"
NEED_SUBJECT_DISCOVERY = "subject_discovery"


@dataclass(frozen=True, slots=True)
class FollowUpEvidenceRequirement:
    requirement_id: str
    subject_hint: str | None
    need_type: str
    required: bool
    reason: str
    requirement_hash: str


@dataclass(frozen=True, slots=True)
class FollowUpEvidenceRequirementProjection:
    session_id: str
    intent: str
    subject_hint: str | None
    requirements: tuple[FollowUpEvidenceRequirement, ...]
    projection_status: str
    projection_hash: str
    read_only: bool


class FollowUpEvidenceRequirementProjector:
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

    def project(
        self,
        intent: ExplanationContinuationIntent,
    ) -> FollowUpEvidenceRequirementProjection:
        if not isinstance(
            intent,
            ExplanationContinuationIntent,
        ):
            raise TypeError(
                "intent must be ExplanationContinuationIntent"
            )

        specs = ()

        if intent.intent == INTENT_MORE_EVIDENCE:
            specs = (
                (
                    NEED_CURRENT_EVIDENCE,
                    True,
                    "preserve_current_support",
                ),
                (
                    NEED_ADDITIONAL_EVIDENCE,
                    True,
                    "expand_evidence_support",
                ),
            )
        elif intent.intent == INTENT_CONTRADICTION:
            specs = (
                (
                    NEED_CURRENT_EVIDENCE,
                    True,
                    "preserve_current_support",
                ),
                (
                    NEED_CONTRADICTORY_EVIDENCE,
                    True,
                    "inspect_conflicting_evidence",
                ),
            )
        elif intent.intent == INTENT_TIMELINE:
            specs = (
                (
                    NEED_CURRENT_EVIDENCE,
                    True,
                    "preserve_current_support",
                ),
                (
                    NEED_TEMPORAL_EVIDENCE,
                    True,
                    "inspect_change_over_time",
                ),
            )
        elif intent.intent == INTENT_CONTINUE:
            specs = (
                (
                    NEED_CURRENT_EVIDENCE,
                    True,
                    "continue_current_explanation",
                ),
            )
        elif intent.intent == INTENT_NEW_SUBJECT:
            specs = (
                (
                    NEED_SUBJECT_DISCOVERY,
                    True,
                    "resolve_new_subject_evidence_scope",
                ),
            )
        elif intent.intent == INTENT_UNRESOLVED:
            specs = ()

        requirements = []

        for index, (
            need_type,
            required,
            reason,
        ) in enumerate(specs, start=1):
            body = {
                "session_id": intent.session_id,
                "intent": intent.intent,
                "subject_hint": (
                    intent.resolved_subject_hint
                ),
                "need_type": need_type,
                "required": required,
                "reason": reason,
                "ordinal": index,
            }

            requirement_hash = deterministic_sha256(body)

            requirements.append(
                FollowUpEvidenceRequirement(
                    requirement_id=(
                        f"req.{requirement_hash[:24]}"
                    ),
                    subject_hint=(
                        intent.resolved_subject_hint
                    ),
                    need_type=need_type,
                    required=required,
                    reason=reason,
                    requirement_hash=requirement_hash,
                )
            )

        requirements = tuple(requirements)

        status = (
            "projected"
            if requirements
            else "unresolved"
        )

        body = {
            "session_id": intent.session_id,
            "intent": intent.intent,
            "subject_hint": intent.resolved_subject_hint,
            "requirement_hashes": tuple(
                item.requirement_hash
                for item in requirements
            ),
            "projection_status": status,
            "read_only": True,
        }

        return FollowUpEvidenceRequirementProjection(
            session_id=intent.session_id,
            intent=intent.intent,
            subject_hint=intent.resolved_subject_hint,
            requirements=requirements,
            projection_status=status,
            projection_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_followup_evidence_requirement_projection() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-064 must remain read-only"
        )

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
        )
    ):
        raise AssertionError(
            "OI-064 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_064_REVISION",
    "NEED_CURRENT_EVIDENCE",
    "NEED_ADDITIONAL_EVIDENCE",
    "NEED_CONTRADICTORY_EVIDENCE",
    "NEED_TEMPORAL_EVIDENCE",
    "NEED_SUBJECT_DISCOVERY",
    "FollowUpEvidenceRequirement",
    "FollowUpEvidenceRequirementProjection",
    "FollowUpEvidenceRequirementProjector",
    "verify_followup_evidence_requirement_projection",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_061_explanation_intent_continuation_classifier import (
    ExplanationContinuationIntent,
    INTENT_MORE_EVIDENCE,
    INTENT_CONTRADICTION,
    INTENT_TIMELINE,
    INTENT_UNRESOLVED,
)
from qseries_v2.observation_intelligence.oi_064_followup_evidence_requirement_projection import (
    OI_064_REVISION,
    NEED_ADDITIONAL_EVIDENCE,
    NEED_CONTRADICTORY_EVIDENCE,
    NEED_TEMPORAL_EVIDENCE,
    FollowUpEvidenceRequirementProjector,
    verify_followup_evidence_requirement_projection,
)


def intent(kind):
    return ExplanationContinuationIntent(
        session_id="session.1",
        raw_followup="follow up",
        intent=kind,
        resolved_subject_hint="Astros strikeouts",
        resolved_query_id="query.astros",
        intent_hash="a" * 64,
        read_only=True,
    )


class TestOI064(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_followup_evidence_requirement_projection()
        )

    def test_more_evidence(self):
        result = FollowUpEvidenceRequirementProjector().project(
            intent(INTENT_MORE_EVIDENCE)
        )

        self.assertIn(
            NEED_ADDITIONAL_EVIDENCE,
            tuple(
                item.need_type
                for item in result.requirements
            ),
        )

    def test_contradiction(self):
        result = FollowUpEvidenceRequirementProjector().project(
            intent(INTENT_CONTRADICTION)
        )

        self.assertIn(
            NEED_CONTRADICTORY_EVIDENCE,
            tuple(
                item.need_type
                for item in result.requirements
            ),
        )

    def test_timeline(self):
        result = FollowUpEvidenceRequirementProjector().project(
            intent(INTENT_TIMELINE)
        )

        self.assertIn(
            NEED_TEMPORAL_EVIDENCE,
            tuple(
                item.need_type
                for item in result.requirements
            ),
        )

    def test_unresolved_fails_closed(self):
        result = FollowUpEvidenceRequirementProjector().project(
            intent(INTENT_UNRESOLVED)
        )

        self.assertEqual(
            result.requirements,
            (),
        )
        self.assertEqual(
            result.projection_status,
            "unresolved",
        )

    def test_deterministic(self):
        projector = FollowUpEvidenceRequirementProjector()

        a = projector.project(
            intent(INTENT_MORE_EVIDENCE)
        )
        b = projector.project(
            intent(INTENT_MORE_EVIDENCE)
        )

        self.assertEqual(
            a.projection_hash,
            b.projection_hash,
        )

    def test_side_effects(self):
        projector = FollowUpEvidenceRequirementProjector()

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


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-064 CERTIFICATION TEST")
    print(" FOLLOW-UP EVIDENCE REQUIREMENT PROJECTION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI064
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-064")
    print(f"[PASS] Revision: {OI_064_REVISION}")
    print("[PASS] Follow-up intents project into explicit generic evidence requirements")
    print("[PASS] More-evidence, contradiction, timeline, continuation, and new-subject needs remain domain-agnostic")
    print("[PASS] Unresolved follow-ups fail closed without inventing evidence requirements")
    print("[DONE] OI-064 CERTIFIED")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_checked(path: Path, source: str) -> None:
    text = source.lstrip()
    ast.parse(text, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"[PASS] Wrote: {path.relative_to(ROOT)}"
    )


def main() -> int:
    print("=" * 72)
    print(" OI-064 INSTALLER")
    print(" FOLLOW-UP EVIDENCE REQUIREMENT PROJECTION")
    print("=" * 72)
    print(
        f"[BOOT] Revision: {INSTALLER_REVISION}"
    )
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
        "[PASS] Certified OI-061 and OI-063 "
        "verified read-only"
    )

    affected = (MODULE, TEST, INIT)
    backups = {
        item: (
            item.read_bytes()
            if item.exists()
            else None
        )
        for item in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = (
            INIT.read_text(encoding="utf-8")
            if INIT.exists()
            else ""
        )

        export = (
            "from .oi_064_followup_evidence_requirement_projection import *"
        )

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"

            current += export + "\n"

            ast.parse(
                current,
                filename=str(INIT),
            )

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

        print(
            "[PASS] In-memory compilation verified"
        )
        print(
            "[PASS] Certified upstream remained unchanged"
        )

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + TEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: "
            f"{install_hash}"
        )

        print(
            "[PASS] Follow-up evidence requirement projection "
            "remains deterministic, read-only, and fail-closed"
        )

        print(
            "[DONE] OI-064 INSTALLATION COMPLETE"
        )

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
            "[ROLLBACK] OI-064 installation failed; "
            "all affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())
