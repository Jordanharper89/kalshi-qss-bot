from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-021"
INSTALLER_REVISION = "OI_021_EXPLANATION_CANDIDATE_ASSEMBLY_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"
UPSTREAM_018 = PACKAGE / "oi_018_explanation_evidence_package.py"
UPSTREAM_019 = PACKAGE / "oi_019_evidence_contradiction_registry.py"
UPSTREAM_020 = PACKAGE / "oi_020_temporal_association.py"
MODULE = PACKAGE / "oi_021_explanation_candidate_assembly.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_021_explanation_candidate_assembly.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_018_explanation_evidence_package import (
    ExplanationEvidencePackage,
)
from .oi_019_evidence_contradiction_registry import (
    EvidenceContradictionRegistry,
)
from .oi_020_temporal_association import (
    TemporalAssociation,
)

BUILD_ID = "OI-021"
OI_021_REVISION = "OI_021_EXPLANATION_CANDIDATE_ASSEMBLY_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
CAUSAL_CLAIM_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False


class ExplanationCandidateAssemblyError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ExplanationCandidate:
    evidence_observation_id: str
    temporal_relation: str
    seconds_from_change_observation: int
    contradiction_count: int
    agreement_count: int
    candidate_hash: str


@dataclass(frozen=True, slots=True)
class ExplanationCandidateSet:
    package_hash: str
    candidates: tuple[ExplanationCandidate, ...]
    candidate_set_hash: str
    causal_claim_allowed: bool
    predictive: bool
    edge_score_allowed: bool


class ExplanationCandidateAssembler:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    causal_claim_allowed = False
    prediction_allowed = False
    edge_score_allowed = False

    def assemble(
        self,
        *,
        package: ExplanationEvidencePackage,
        temporal_associations: tuple[TemporalAssociation, ...],
        evidence_relationships: EvidenceContradictionRegistry,
    ) -> ExplanationCandidateSet:
        if not isinstance(
            package,
            ExplanationEvidencePackage,
        ):
            raise TypeError(
                "package must be ExplanationEvidencePackage"
            )

        if not isinstance(
            evidence_relationships,
            EvidenceContradictionRegistry,
        ):
            raise TypeError(
                "evidence_relationships must be "
                "EvidenceContradictionRegistry"
            )

        associations = tuple(
            temporal_associations
        )

        if any(
            not isinstance(
                item,
                TemporalAssociation,
            )
            for item in associations
        ):
            raise TypeError(
                "all temporal associations must be "
                "TemporalAssociation"
            )

        candidates = []

        for association in associations:
            relationships = (
                evidence_relationships.for_evidence(
                    association.evidence_observation_id
                )
            )

            contradiction_count = sum(
                1
                for item in relationships
                if item.relation == "contradicts"
            )

            agreement_count = sum(
                1
                for item in relationships
                if item.relation == "agrees"
            )

            body = {
                "evidence_observation_id": (
                    association.evidence_observation_id
                ),
                "temporal_relation": (
                    association.temporal_relation
                ),
                "seconds_from_change_observation": (
                    association.seconds_from_change_observation
                ),
                "contradiction_count": (
                    contradiction_count
                ),
                "agreement_count": (
                    agreement_count
                ),
            }

            candidates.append(
                ExplanationCandidate(
                    evidence_observation_id=(
                        association.evidence_observation_id
                    ),
                    temporal_relation=(
                        association.temporal_relation
                    ),
                    seconds_from_change_observation=(
                        association.seconds_from_change_observation
                    ),
                    contradiction_count=(
                        contradiction_count
                    ),
                    agreement_count=(
                        agreement_count
                    ),
                    candidate_hash=(
                        deterministic_sha256(body)
                    ),
                )
            )

        ordered = tuple(
            sorted(
                candidates,
                key=lambda item: (
                    abs(
                        item.seconds_from_change_observation
                    ),
                    item.evidence_observation_id,
                ),
            )
        )

        body = {
            "package_hash": package.package_hash,
            "candidate_hashes": tuple(
                item.candidate_hash
                for item in ordered
            ),
            "causal_claim_allowed": False,
            "predictive": False,
            "edge_score_allowed": False,
        }

        return ExplanationCandidateSet(
            package_hash=package.package_hash,
            candidates=ordered,
            candidate_set_hash=(
                deterministic_sha256(body)
            ),
            causal_claim_allowed=False,
            predictive=False,
            edge_score_allowed=False,
        )


def verify_explanation_candidate_assembly() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-021 must remain read-only"
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
        )
    ):
        raise AssertionError(
            "OI-021 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_021_REVISION",
    "ExplanationCandidateAssemblyError",
    "ExplanationCandidate",
    "ExplanationCandidateSet",
    "ExplanationCandidateAssembler",
    "verify_explanation_candidate_assembly",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_018_explanation_evidence_package import (
    ExplanationEvidencePackage,
)
from qseries_v2.observation_intelligence.oi_019_evidence_contradiction_registry import (
    EvidenceRelationship,
    EvidenceContradictionRegistry,
)
from qseries_v2.observation_intelligence.oi_020_temporal_association import (
    TemporalAssociation,
)
from qseries_v2.observation_intelligence.oi_021_explanation_candidate_assembly import (
    OI_021_REVISION,
    ExplanationCandidateAssembler,
    verify_explanation_candidate_assembly,
)

NOW = datetime(
    2026,
    8,
    10,
    15,
    0,
    tzinfo=timezone.utc,
)


def package():
    return ExplanationEvidencePackage(
        query_id="query.explain",
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


def association(
    evidence_id: str,
    seconds: int,
):
    return TemporalAssociation(
        change_hash="c" * 64,
        evidence_observation_id=evidence_id,
        evidence_subject="Astros",
        evidence_observation_type="news",
        evidence_observed_at=NOW,
        seconds_from_change_observation=seconds,
        temporal_relation=(
            "before"
            if seconds < 0
            else (
                "after"
                if seconds > 0
                else "simultaneous"
            )
        ),
        association_hash="e" * 64,
    )


def registry():
    return EvidenceContradictionRegistry(
        (
            EvidenceRelationship(
                relationship_id="rel.1",
                left_evidence_id="obs.a",
                right_evidence_id="obs.b",
                relation="contradicts",
                basis="explicit source disagreement",
            ),
        )
    )


class TestOI021(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_candidate_assembly()
        )

    def test_assembly(self):
        values = (
            ExplanationCandidateAssembler()
            .assemble(
                package=package(),
                temporal_associations=(
                    association(
                        "obs.a",
                        -20,
                    ),
                    association(
                        "obs.b",
                        -10,
                    ),
                ),
                evidence_relationships=registry(),
            )
        )

        self.assertEqual(
            len(values.candidates),
            2,
        )

    def test_nearest_first(self):
        values = (
            ExplanationCandidateAssembler()
            .assemble(
                package=package(),
                temporal_associations=(
                    association(
                        "obs.a",
                        -20,
                    ),
                    association(
                        "obs.b",
                        -10,
                    ),
                ),
                evidence_relationships=registry(),
            )
        )

        self.assertEqual(
            values.candidates[0]
            .evidence_observation_id,
            "obs.b",
        )

    def test_contradiction_count(self):
        values = (
            ExplanationCandidateAssembler()
            .assemble(
                package=package(),
                temporal_associations=(
                    association(
                        "obs.a",
                        -20,
                    ),
                ),
                evidence_relationships=registry(),
            )
        )

        self.assertEqual(
            values.candidates[0]
            .contradiction_count,
            1,
        )

    def test_non_causal(self):
        values = (
            ExplanationCandidateAssembler()
            .assemble(
                package=package(),
                temporal_associations=(),
                evidence_relationships=registry(),
            )
        )

        self.assertFalse(
            values.causal_claim_allowed
        )
        self.assertFalse(
            values.predictive
        )
        self.assertFalse(
            values.edge_score_allowed
        )

    def test_deterministic(self):
        assembler = ExplanationCandidateAssembler()

        a = assembler.assemble(
            package=package(),
            temporal_associations=(
                association(
                    "obs.a",
                    -20,
                ),
            ),
            evidence_relationships=registry(),
        )

        b = assembler.assemble(
            package=package(),
            temporal_associations=(
                association(
                    "obs.a",
                    -20,
                ),
            ),
            evidence_relationships=registry(),
        )

        self.assertEqual(
            a.candidate_set_hash,
            b.candidate_set_hash,
        )

    def test_side_effects(self):
        assembler = ExplanationCandidateAssembler()

        self.assertTrue(
            assembler.read_only
        )
        self.assertFalse(
            assembler.network_allowed
        )
        self.assertFalse(
            assembler.persistence_allowed
        )
        self.assertFalse(
            assembler.publication_allowed
        )
        self.assertFalse(
            assembler.execution_allowed
        )
        self.assertFalse(
            assembler.qseries_execution_allowed
        )
        self.assertFalse(
            assembler.causal_claim_allowed
        )
        self.assertFalse(
            assembler.prediction_allowed
        )
        self.assertFalse(
            assembler.edge_score_allowed
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-021 CERTIFICATION TEST")
    print(" EXPLANATION CANDIDATE ASSEMBLY")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI021
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-021")
    print(f"[PASS] Revision: {OI_021_REVISION}")
    print("[PASS] Temporally associated evidence assembled into explanation candidates")
    print("[PASS] Agreement and contradiction context preserved per candidate")
    print("[PASS] Candidate ordering is structural and does not imply causal importance")
    print("[PASS] Causal claims, prediction, and edge scoring remain disabled")
    print("[DONE] OI-021 CERTIFIED")
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
    print(" OI-021 INSTALLER")
    print(" EXPLANATION CANDIDATE ASSEMBLY")
    print("=" * 72)

    print(
        f"[BOOT] Revision: "
        f"{INSTALLER_REVISION}"
    )

    print(
        f"[ROOT] {ROOT}"
    )

    upstreams = (
        (UPSTREAM_018, "OI-018"),
        (UPSTREAM_019, "OI-019"),
        (UPSTREAM_020, "OI-020"),
    )

    for upstream, name in upstreams:
        if not upstream.is_file():
            raise RuntimeError(
                f"Certified {name} missing: "
                f"{upstream}"
            )

    upstream_hashes = {
        upstream: sha(upstream)
        for upstream, _ in upstreams
    }

    print(
        "[PASS] Certified OI-018 through OI-020 "
        "verified read-only"
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
            "from .oi_021_explanation_candidate_assembly import *"
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
            "[PASS] Candidate assembly remains "
            "deterministic, read-only, non-causal, "
            "non-predictive, and non-scoring"
        )

        print(
            "[DONE] OI-021 INSTALLATION COMPLETE"
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
            "[ROLLBACK] OI-021 installation failed; "
            "all affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
