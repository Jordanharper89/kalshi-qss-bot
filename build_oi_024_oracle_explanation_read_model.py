from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-024"
INSTALLER_REVISION = "OI_024_ORACLE_EXPLANATION_READ_MODEL_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_018_explanation_evidence_package.py", "OI-018"),
    (PACKAGE / "oi_022_evidence_narrative_assembly.py", "OI-022"),
    (PACKAGE / "oi_023_evidence_confidence_composition.py", "OI-023"),
)

MODULE = PACKAGE / "oi_024_oracle_explanation_read_model.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_024_oracle_explanation_read_model.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_018_explanation_evidence_package import ExplanationEvidencePackage
from .oi_022_evidence_narrative_assembly import EvidenceNarrative
from .oi_023_evidence_confidence_composition import EvidenceConfidenceProfile

BUILD_ID = "OI-024"
OI_024_REVISION = "OI_024_ORACLE_EXPLANATION_READ_MODEL_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
CAUSAL_CLAIM_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False


class OracleExplanationReadModelError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class OracleExplanationTimelineEntry:
    ordinal: int
    evidence_observation_id: str
    temporal_relation: str
    seconds_from_change_observation: int
    agreement_count: int
    contradiction_count: int


@dataclass(frozen=True, slots=True)
class OracleExplanationReadModel:
    query_id: str
    profile_id: str
    built_at: datetime
    sufficient_evidence: bool
    completeness_status: str
    evidence_item_count: int
    distinct_source_count: int
    stale_evidence_count: int
    supporting_relationship_count: int
    contradicting_relationship_count: int
    timeline: tuple[OracleExplanationTimelineEntry, ...]
    missing_required_evidence: bool
    read_model_hash: str
    causal_claim_allowed: bool
    predictive: bool
    edge_score_allowed: bool
    probability_allowed: bool
    read_only: bool


class OracleExplanationReadModelBuilder:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    causal_claim_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False

    def build(
        self,
        *,
        package: ExplanationEvidencePackage,
        narrative: EvidenceNarrative,
        confidence: EvidenceConfidenceProfile,
        built_at: datetime,
    ) -> OracleExplanationReadModel:
        if not isinstance(package, ExplanationEvidencePackage):
            raise TypeError(
                "package must be ExplanationEvidencePackage"
            )

        if not isinstance(narrative, EvidenceNarrative):
            raise TypeError(
                "narrative must be EvidenceNarrative"
            )

        if not isinstance(confidence, EvidenceConfidenceProfile):
            raise TypeError(
                "confidence must be EvidenceConfidenceProfile"
            )

        if narrative.package_hash != package.package_hash:
            raise OracleExplanationReadModelError(
                "narrative does not belong to explanation package"
            )

        if confidence.narrative_hash != narrative.narrative_hash:
            raise OracleExplanationReadModelError(
                "confidence profile does not belong to narrative"
            )

        if not isinstance(built_at, datetime):
            raise TypeError(
                "built_at must be datetime"
            )

        if built_at.tzinfo is None:
            raise OracleExplanationReadModelError(
                "built_at must be timezone-aware"
            )

        built_at = built_at.astimezone(
            timezone.utc
        )

        timeline = tuple(
            OracleExplanationTimelineEntry(
                ordinal=item.ordinal,
                evidence_observation_id=(
                    item.evidence_observation_id
                ),
                temporal_relation=(
                    item.temporal_relation
                ),
                seconds_from_change_observation=(
                    item.seconds_from_change_observation
                ),
                agreement_count=item.agreement_count,
                contradiction_count=(
                    item.contradiction_count
                ),
            )
            for item in narrative.entries
        )

        missing_required = (
            not package.sufficient_evidence
        )

        body = {
            "query_id": package.query_id,
            "profile_id": package.profile_id,
            "built_at": built_at,
            "sufficient_evidence": (
                package.sufficient_evidence
            ),
            "completeness_status": (
                confidence.completeness_status
            ),
            "evidence_item_count": (
                confidence.evidence_item_count
            ),
            "distinct_source_count": (
                confidence.distinct_source_count
            ),
            "stale_evidence_count": (
                confidence.stale_evidence_count
            ),
            "supporting_relationship_count": (
                confidence.supporting_relationship_count
            ),
            "contradicting_relationship_count": (
                confidence.contradicting_relationship_count
            ),
            "timeline": tuple(
                (
                    item.ordinal,
                    item.evidence_observation_id,
                    item.temporal_relation,
                    item.seconds_from_change_observation,
                    item.agreement_count,
                    item.contradiction_count,
                )
                for item in timeline
            ),
            "missing_required_evidence": (
                missing_required
            ),
            "causal_claim_allowed": False,
            "predictive": False,
            "edge_score_allowed": False,
            "probability_allowed": False,
            "read_only": True,
        }

        return OracleExplanationReadModel(
            query_id=package.query_id,
            profile_id=package.profile_id,
            built_at=built_at,
            sufficient_evidence=(
                package.sufficient_evidence
            ),
            completeness_status=(
                confidence.completeness_status
            ),
            evidence_item_count=(
                confidence.evidence_item_count
            ),
            distinct_source_count=(
                confidence.distinct_source_count
            ),
            stale_evidence_count=(
                confidence.stale_evidence_count
            ),
            supporting_relationship_count=(
                confidence.supporting_relationship_count
            ),
            contradicting_relationship_count=(
                confidence.contradicting_relationship_count
            ),
            timeline=timeline,
            missing_required_evidence=(
                missing_required
            ),
            read_model_hash=(
                deterministic_sha256(body)
            ),
            causal_claim_allowed=False,
            predictive=False,
            edge_score_allowed=False,
            probability_allowed=False,
            read_only=True,
        )


def verify_oracle_explanation_read_model() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-024 must remain read-only"
        )

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
            CAUSAL_CLAIM_ALLOWED,
            PREDICTION_ALLOWED,
            EDGE_SCORE_ALLOWED,
            PROBABILITY_ALLOWED,
        )
    ):
        raise AssertionError(
            "OI-024 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_024_REVISION",
    "OracleExplanationReadModelError",
    "OracleExplanationTimelineEntry",
    "OracleExplanationReadModel",
    "OracleExplanationReadModelBuilder",
    "verify_oracle_explanation_read_model",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_018_explanation_evidence_package import (
    ExplanationEvidencePackage,
)
from qseries_v2.observation_intelligence.oi_022_evidence_narrative_assembly import (
    NarrativeEvidenceEntry,
    EvidenceNarrative,
)
from qseries_v2.observation_intelligence.oi_023_evidence_confidence_composition import (
    EvidenceConfidenceProfile,
)
from qseries_v2.observation_intelligence.oi_024_oracle_explanation_read_model import (
    OI_024_REVISION,
    OracleExplanationReadModelBuilder,
    verify_oracle_explanation_read_model,
)

NOW = datetime(
    2026,
    8,
    10,
    17,
    0,
    tzinfo=timezone.utc,
)


def package():
    return ExplanationEvidencePackage(
        query_id="query.astros",
        profile_id="profile.market_explanation",
        built_at=NOW,
        reasoning_input_hash="a" * 64,
        sufficiency_decision_hash="b" * 64,
        sufficient_evidence=True,
        evidence_item_count=2,
        change_hashes=("c" * 64,),
        package_hash="d" * 64,
        causal_claim_allowed=False,
        predictive=False,
        read_only=True,
    )


def narrative():
    return EvidenceNarrative(
        package_hash="d" * 64,
        candidate_set_hash="e" * 64,
        entries=(
            NarrativeEvidenceEntry(
                ordinal=1,
                evidence_observation_id="obs.a",
                temporal_relation="before",
                seconds_from_change_observation=-20,
                agreement_count=1,
                contradiction_count=0,
                entry_hash="f" * 64,
            ),
        ),
        supporting_relationship_count=1,
        contradicting_relationship_count=0,
        narrative_hash="1" * 64,
        causal_claim_allowed=False,
        predictive=False,
        edge_score_allowed=False,
        read_only=True,
    )


def confidence():
    return EvidenceConfidenceProfile(
        sufficiency_decision_hash="b" * 64,
        narrative_hash="1" * 64,
        evidence_item_count=2,
        distinct_source_count=2,
        stale_evidence_count=0,
        supporting_relationship_count=1,
        contradicting_relationship_count=0,
        completeness_status="complete",
        confidence_hash="2" * 64,
        predictive=False,
        edge_score_allowed=False,
        probability_allowed=False,
        read_only=True,
    )


class TestOI024(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oracle_explanation_read_model()
        )

    def test_build(self):
        model = OracleExplanationReadModelBuilder().build(
            package=package(),
            narrative=narrative(),
            confidence=confidence(),
            built_at=NOW,
        )

        self.assertEqual(
            model.query_id,
            "query.astros",
        )

        self.assertEqual(
            model.completeness_status,
            "complete",
        )

        self.assertEqual(
            len(model.timeline),
            1,
        )

    def test_counts(self):
        model = OracleExplanationReadModelBuilder().build(
            package=package(),
            narrative=narrative(),
            confidence=confidence(),
            built_at=NOW,
        )

        self.assertEqual(
            model.evidence_item_count,
            2,
        )

        self.assertEqual(
            model.distinct_source_count,
            2,
        )

        self.assertEqual(
            model.supporting_relationship_count,
            1,
        )

    def test_non_predictive(self):
        model = OracleExplanationReadModelBuilder().build(
            package=package(),
            narrative=narrative(),
            confidence=confidence(),
            built_at=NOW,
        )

        self.assertFalse(
            model.causal_claim_allowed
        )

        self.assertFalse(
            model.predictive
        )

        self.assertFalse(
            model.edge_score_allowed
        )

        self.assertFalse(
            model.probability_allowed
        )

        self.assertTrue(
            model.read_only
        )

    def test_deterministic(self):
        builder = OracleExplanationReadModelBuilder()

        a = builder.build(
            package=package(),
            narrative=narrative(),
            confidence=confidence(),
            built_at=NOW,
        )

        b = builder.build(
            package=package(),
            narrative=narrative(),
            confidence=confidence(),
            built_at=NOW,
        )

        self.assertEqual(
            a.read_model_hash,
            b.read_model_hash,
        )

    def test_side_effects(self):
        builder = OracleExplanationReadModelBuilder()

        self.assertTrue(
            builder.read_only
        )

        self.assertFalse(
            builder.network_allowed
        )

        self.assertFalse(
            builder.persistence_allowed
        )

        self.assertFalse(
            builder.publication_allowed
        )

        self.assertFalse(
            builder.execution_allowed
        )

        self.assertFalse(
            builder.qseries_execution_allowed
        )

        self.assertFalse(
            builder.causal_claim_allowed
        )

        self.assertFalse(
            builder.prediction_allowed
        )

        self.assertFalse(
            builder.edge_score_allowed
        )

        self.assertFalse(
            builder.probability_allowed
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-024 CERTIFICATION TEST")
    print(" ORACLE EXPLANATION READ MODEL")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI024
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-024")
    print(f"[PASS] Revision: {OI_024_REVISION}")
    print("[PASS] Explanation-ready Oracle read model certified")
    print("[PASS] Timeline, evidence completeness, source diversity, freshness, support, and contradiction preserved")
    print("[PASS] Causal claims, prediction probability, and edge scoring remain disabled")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-024 CERTIFIED")
"""


def sha(
    path: Path,
) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def write_checked(
    path: Path,
    source: str,
) -> None:
    text = source.lstrip()

    ast.parse(
        text,
        filename=str(path),
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )

    print(
        f"[PASS] Wrote: "
        f"{path.relative_to(ROOT)}"
    )


def main() -> int:
    print("=" * 72)
    print(" OI-024 INSTALLER")
    print(" ORACLE EXPLANATION READ MODEL")
    print("=" * 72)

    print(
        f"[BOOT] Revision: "
        f"{INSTALLER_REVISION}"
    )

    print(
        f"[ROOT] {ROOT}"
    )

    for upstream, name in UPSTREAMS:
        if not upstream.is_file():
            raise RuntimeError(
                f"Certified {name} missing: "
                f"{upstream}"
            )

    upstream_hashes = {
        upstream: sha(upstream)
        for upstream, _ in UPSTREAMS
    }

    print(
        "[PASS] Certified OI-018, OI-022, "
        "and OI-023 verified read-only"
    )

    affected = (
        MODULE,
        TEST,
        INIT,
    )

    backups = {
        item: (
            item.read_bytes()
            if item.exists()
            else None
        )
        for item in affected
    }

    try:
        write_checked(
            MODULE,
            MODULE_SOURCE,
        )

        write_checked(
            TEST,
            TEST_SOURCE,
        )

        current = (
            INIT.read_text(
                encoding="utf-8"
            )
            if INIT.exists()
            else ""
        )

        export = (
            "from .oi_024_oracle_explanation_read_model import *"
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
            MODULE.read_text(
                encoding="utf-8"
            ),
            str(MODULE),
            "exec",
        )

        compile(
            TEST.read_text(
                encoding="utf-8"
            ),
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
            "[PASS] Explanation read model remains "
            "deterministic, read-only, non-causal, "
            "non-predictive, and non-scoring"
        )

        print(
            "[DONE] OI-024 INSTALLATION COMPLETE"
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

                item.write_bytes(
                    original
                )

        print(
            "[ROLLBACK] OI-024 installation failed; "
            "all affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
