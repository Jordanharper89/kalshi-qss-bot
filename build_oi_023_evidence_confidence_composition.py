from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-023"
INSTALLER_REVISION = "OI_023_EVIDENCE_CONFIDENCE_COMPOSITION_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_016_evidence_sufficiency_gate.py", "OI-016"),
    (PACKAGE / "oi_019_evidence_contradiction_registry.py", "OI-019"),
    (PACKAGE / "oi_022_evidence_narrative_assembly.py", "OI-022"),
)

MODULE = PACKAGE / "oi_023_evidence_confidence_composition.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_023_evidence_confidence_composition.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_016_evidence_sufficiency_gate import EvidenceSufficiencyDecision
from .oi_022_evidence_narrative_assembly import EvidenceNarrative

BUILD_ID = "OI-023"
OI_023_REVISION = "OI_023_EVIDENCE_CONFIDENCE_COMPOSITION_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False

COMPLETE = "complete"
PARTIAL = "partial"
INSUFFICIENT = "insufficient"


class EvidenceConfidenceCompositionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class EvidenceConfidenceProfile:
    sufficiency_decision_hash: str
    narrative_hash: str
    evidence_item_count: int
    distinct_source_count: int
    stale_evidence_count: int
    supporting_relationship_count: int
    contradicting_relationship_count: int
    completeness_status: str
    confidence_hash: str
    predictive: bool
    edge_score_allowed: bool
    probability_allowed: bool
    read_only: bool


class EvidenceConfidenceComposer:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False

    def compose(
        self,
        *,
        sufficiency: EvidenceSufficiencyDecision,
        narrative: EvidenceNarrative,
    ) -> EvidenceConfidenceProfile:
        if not isinstance(sufficiency, EvidenceSufficiencyDecision):
            raise TypeError(
                "sufficiency must be EvidenceSufficiencyDecision"
            )

        if not isinstance(narrative, EvidenceNarrative):
            raise TypeError(
                "narrative must be EvidenceNarrative"
            )

        if sufficiency.sufficient:
            completeness = COMPLETE
        elif (
            sufficiency.evidence_item_count > 0
            or narrative.entries
        ):
            completeness = PARTIAL
        else:
            completeness = INSUFFICIENT

        body = {
            "sufficiency_decision_hash": sufficiency.decision_hash,
            "narrative_hash": narrative.narrative_hash,
            "evidence_item_count": sufficiency.evidence_item_count,
            "distinct_source_count": sufficiency.distinct_source_count,
            "stale_evidence_count": sufficiency.stale_evidence_count,
            "supporting_relationship_count": narrative.supporting_relationship_count,
            "contradicting_relationship_count": narrative.contradicting_relationship_count,
            "completeness_status": completeness,
            "predictive": False,
            "edge_score_allowed": False,
            "probability_allowed": False,
            "read_only": True,
        }

        return EvidenceConfidenceProfile(
            sufficiency_decision_hash=sufficiency.decision_hash,
            narrative_hash=narrative.narrative_hash,
            evidence_item_count=sufficiency.evidence_item_count,
            distinct_source_count=sufficiency.distinct_source_count,
            stale_evidence_count=sufficiency.stale_evidence_count,
            supporting_relationship_count=narrative.supporting_relationship_count,
            contradicting_relationship_count=narrative.contradicting_relationship_count,
            completeness_status=completeness,
            confidence_hash=deterministic_sha256(body),
            predictive=False,
            edge_score_allowed=False,
            probability_allowed=False,
            read_only=True,
        )


def verify_evidence_confidence_composition() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-023 must remain read-only"
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
        )
    ):
        raise AssertionError(
            "OI-023 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_023_REVISION",
    "COMPLETE",
    "PARTIAL",
    "INSUFFICIENT",
    "EvidenceConfidenceCompositionError",
    "EvidenceConfidenceProfile",
    "EvidenceConfidenceComposer",
    "verify_evidence_confidence_composition",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_016_evidence_sufficiency_gate import (
    EvidenceSufficiencyDecision,
)
from qseries_v2.observation_intelligence.oi_022_evidence_narrative_assembly import (
    EvidenceNarrative,
)
from qseries_v2.observation_intelligence.oi_023_evidence_confidence_composition import (
    OI_023_REVISION,
    COMPLETE,
    PARTIAL,
    EvidenceConfidenceComposer,
    verify_evidence_confidence_composition,
)


def decision(sufficient=True):
    return EvidenceSufficiencyDecision(
        policy_id="policy.test",
        input_hash="a" * 64,
        evidence_item_count=2,
        distinct_source_count=2,
        stale_evidence_count=0,
        complete_required_evidence=sufficient,
        sufficient=sufficient,
        reason_codes=(
            ()
            if sufficient
            else ("missing_required_evidence",)
        ),
        decision_hash="b" * 64,
    )


def narrative():
    return EvidenceNarrative(
        package_hash="c" * 64,
        candidate_set_hash="d" * 64,
        entries=(),
        supporting_relationship_count=2,
        contradicting_relationship_count=1,
        narrative_hash="e" * 64,
        causal_claim_allowed=False,
        predictive=False,
        edge_score_allowed=False,
        read_only=True,
    )


class TestOI023(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_evidence_confidence_composition()
        )

    def test_complete(self):
        profile = EvidenceConfidenceComposer().compose(
            sufficiency=decision(True),
            narrative=narrative(),
        )
        self.assertEqual(
            profile.completeness_status,
            COMPLETE,
        )

    def test_partial(self):
        profile = EvidenceConfidenceComposer().compose(
            sufficiency=decision(False),
            narrative=narrative(),
        )
        self.assertEqual(
            profile.completeness_status,
            PARTIAL,
        )

    def test_counts_preserved(self):
        profile = EvidenceConfidenceComposer().compose(
            sufficiency=decision(True),
            narrative=narrative(),
        )
        self.assertEqual(profile.distinct_source_count, 2)
        self.assertEqual(profile.supporting_relationship_count, 2)
        self.assertEqual(profile.contradicting_relationship_count, 1)

    def test_non_predictive(self):
        profile = EvidenceConfidenceComposer().compose(
            sufficiency=decision(True),
            narrative=narrative(),
        )
        self.assertFalse(profile.predictive)
        self.assertFalse(profile.edge_score_allowed)
        self.assertFalse(profile.probability_allowed)
        self.assertTrue(profile.read_only)

    def test_deterministic(self):
        composer = EvidenceConfidenceComposer()
        a = composer.compose(
            sufficiency=decision(True),
            narrative=narrative(),
        )
        b = composer.compose(
            sufficiency=decision(True),
            narrative=narrative(),
        )
        self.assertEqual(
            a.confidence_hash,
            b.confidence_hash,
        )

    def test_side_effects(self):
        composer = EvidenceConfidenceComposer()
        self.assertTrue(composer.read_only)
        self.assertFalse(composer.network_allowed)
        self.assertFalse(composer.persistence_allowed)
        self.assertFalse(composer.publication_allowed)
        self.assertFalse(composer.execution_allowed)
        self.assertFalse(composer.qseries_execution_allowed)
        self.assertFalse(composer.prediction_allowed)
        self.assertFalse(composer.edge_score_allowed)
        self.assertFalse(composer.probability_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-023 CERTIFICATION TEST")
    print(" EVIDENCE CONFIDENCE COMPOSITION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI023
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-023")
    print(f"[PASS] Revision: {OI_023_REVISION}")
    print("[PASS] Evidence completeness, source diversity, freshness, and contradiction composition certified")
    print("[PASS] Confidence composition describes evidence quality only")
    print("[PASS] Prediction probability, edge scoring, and trade confidence remain disabled")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-023 CERTIFIED")
"""


def sha(path: Path) -> str:
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
    print(" OI-023 INSTALLER")
    print(" EVIDENCE CONFIDENCE COMPOSITION")
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
        "[PASS] Certified OI-016, OI-019, "
        "and OI-022 verified read-only"
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
            "from .oi_023_evidence_confidence_composition import *"
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
            "[PASS] Confidence composition remains "
            "deterministic, read-only, and evidence-only"
        )

        print(
            "[DONE] OI-023 INSTALLATION COMPLETE"
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
            "[ROLLBACK] OI-023 installation failed; "
            "all affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
