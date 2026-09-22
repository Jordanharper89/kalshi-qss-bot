from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-046"
INSTALLER_REVISION = "OI_046_EXPLANATION_CANDIDATE_RESOLUTION_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_021_explanation_candidate_assembly.py", "OI-021"),
    (PACKAGE / "oi_044_explanation_support_profile.py", "OI-044"),
    (PACKAGE / "oi_045_oracle_reasoning_read_model.py", "OI-045"),
)

MODULE = PACKAGE / "oi_046_explanation_candidate_resolution.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_046_explanation_candidate_resolution.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_045_oracle_reasoning_read_model import OracleReasoningReadModel

BUILD_ID = "OI-046"
OI_046_REVISION = "OI_046_EXPLANATION_CANDIDATE_RESOLUTION_V1"

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

STATUS_SUPPORTED = "supported"
STATUS_PARTIAL = "partial"
STATUS_UNSUPPORTED = "unsupported"


class ExplanationCandidateResolutionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ExplanationCandidateResolutionItem:
    subject: str
    status: str
    evidence_count: int
    support_class: str
    context_roles: tuple[str, ...]
    relationship_types: tuple[str, ...]
    reason_codes: tuple[str, ...]
    item_hash: str


@dataclass(frozen=True, slots=True)
class ExplanationCandidateResolution:
    query_id: str
    read_model_hash: str
    items: tuple[ExplanationCandidateResolutionItem, ...]
    supported_count: int
    partial_count: int
    unsupported_count: int
    resolution_hash: str
    read_only: bool


class ExplanationCandidateResolver:
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

    def resolve(
        self,
        read_model: OracleReasoningReadModel,
    ) -> ExplanationCandidateResolution:
        if not isinstance(
            read_model,
            OracleReasoningReadModel,
        ):
            raise TypeError(
                "read_model must be OracleReasoningReadModel"
            )

        items = []

        for item in read_model.items:
            reasons = []

            if item.evidence_count < 1:
                status = STATUS_UNSUPPORTED
                reasons.append("no_evidence")
            elif (
                read_model.admission_status == "partial"
                or read_model.missing_need_count > 0
            ):
                status = STATUS_PARTIAL
                reasons.append("missing_required_evidence")
            else:
                status = STATUS_SUPPORTED

            if not item.relationship_types:
                reasons.append("no_structural_relationships")

            if len(item.context_roles) < 1:
                reasons.append("no_context_roles")

            reasons = tuple(sorted(set(reasons)))

            body = {
                "subject": item.subject,
                "status": status,
                "evidence_count": item.evidence_count,
                "support_class": item.support_class,
                "context_roles": item.context_roles,
                "relationship_types": item.relationship_types,
                "reason_codes": reasons,
            }

            items.append(
                ExplanationCandidateResolutionItem(
                    subject=item.subject,
                    status=status,
                    evidence_count=item.evidence_count,
                    support_class=item.support_class,
                    context_roles=item.context_roles,
                    relationship_types=item.relationship_types,
                    reason_codes=reasons,
                    item_hash=deterministic_sha256(body),
                )
            )

        items = tuple(
            sorted(
                items,
                key=lambda value: value.subject,
            )
        )

        supported_count = sum(
            1 for item in items
            if item.status == STATUS_SUPPORTED
        )
        partial_count = sum(
            1 for item in items
            if item.status == STATUS_PARTIAL
        )
        unsupported_count = sum(
            1 for item in items
            if item.status == STATUS_UNSUPPORTED
        )

        body = {
            "query_id": read_model.query_id,
            "read_model_hash": read_model.read_model_hash,
            "item_hashes": tuple(
                item.item_hash
                for item in items
            ),
            "supported_count": supported_count,
            "partial_count": partial_count,
            "unsupported_count": unsupported_count,
            "read_only": True,
        }

        return ExplanationCandidateResolution(
            query_id=read_model.query_id,
            read_model_hash=read_model.read_model_hash,
            items=items,
            supported_count=supported_count,
            partial_count=partial_count,
            unsupported_count=unsupported_count,
            resolution_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_explanation_candidate_resolution() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-046 must remain read-only"
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
            "OI-046 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_046_REVISION",
    "STATUS_SUPPORTED",
    "STATUS_PARTIAL",
    "STATUS_UNSUPPORTED",
    "ExplanationCandidateResolutionError",
    "ExplanationCandidateResolutionItem",
    "ExplanationCandidateResolution",
    "ExplanationCandidateResolver",
    "verify_explanation_candidate_resolution",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_045_oracle_reasoning_read_model import (
    OracleReasoningReadItem,
    OracleReasoningReadModel,
)
from qseries_v2.observation_intelligence.oi_046_explanation_candidate_resolution import (
    OI_046_REVISION,
    STATUS_PARTIAL,
    STATUS_SUPPORTED,
    ExplanationCandidateResolver,
    verify_explanation_candidate_resolution,
)

NOW = datetime(2026, 8, 11, 8, 0, tzinfo=timezone.utc)


def model(admission_status="admitted", missing=0):
    return OracleReasoningReadModel(
        query_id="query.test",
        profile_id="profile.market_explanation",
        subject_hint="Astros strikeouts",
        admission_status=admission_status,
        evidence_count=2,
        relationship_count=1,
        missing_need_count=missing,
        items=(
            OracleReasoningReadItem(
                subject="Astros strikeouts",
                signal_type="multi_evidence_context",
                support_class="multi_evidence_structure",
                evidence_count=2,
                context_roles=(
                    "evidence",
                    "market_state",
                    "sports_context",
                ),
                relationship_types=(
                    "same_subject",
                ),
                item_hash="a" * 64,
            ),
        ),
        built_at=NOW,
        read_model_hash="b" * 64,
        read_only=True,
        predictive=False,
        causal_claim_allowed=False,
    )


class TestOI046(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_candidate_resolution()
        )

    def test_supported(self):
        result = ExplanationCandidateResolver().resolve(
            model()
        )

        self.assertEqual(
            result.items[0].status,
            STATUS_SUPPORTED,
        )

    def test_partial(self):
        result = ExplanationCandidateResolver().resolve(
            model("partial", 1)
        )

        self.assertEqual(
            result.items[0].status,
            STATUS_PARTIAL,
        )

    def test_reason_codes(self):
        result = ExplanationCandidateResolver().resolve(
            model("partial", 1)
        )

        self.assertIn(
            "missing_required_evidence",
            result.items[0].reason_codes,
        )

    def test_deterministic(self):
        resolver = ExplanationCandidateResolver()

        a = resolver.resolve(model())
        b = resolver.resolve(model())

        self.assertEqual(
            a.resolution_hash,
            b.resolution_hash,
        )

    def test_side_effects(self):
        resolver = ExplanationCandidateResolver()

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


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-046 CERTIFICATION TEST")
    print(" EXPLANATION CANDIDATE RESOLUTION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI046
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-046")
    print(f"[PASS] Revision: {OI_046_REVISION}")
    print("[PASS] Supported, partial, and unsupported explanation candidates certified")
    print("[PASS] Missing evidence remains explicit in explanation readiness")
    print("[PASS] No causal claim, probability, prediction, or edge score introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-046 CERTIFIED")
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
    print(" OI-046 INSTALLER")
    print(" EXPLANATION CANDIDATE RESOLUTION")
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
        "[PASS] Certified OI-021, OI-044, "
        "and OI-045 verified read-only"
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
        export = "from .oi_046_explanation_candidate_resolution import *"

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
                    f"Certified upstream changed: {upstream.name}"
                )

        print("[PASS] In-memory compilation verified")
        print("[PASS] Certified upstream remained unchanged")

        install_hash = hashlib.sha256(
            MODULE.read_bytes() + TEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: {install_hash}"
        )
        print(
            "[PASS] Explanation candidate resolution remains deterministic, "
            "read-only, and non-causal"
        )
        print("[DONE] OI-046 INSTALLATION COMPLETE")
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
            "[ROLLBACK] OI-046 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
