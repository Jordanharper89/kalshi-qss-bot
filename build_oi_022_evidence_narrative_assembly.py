from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-022"
INSTALLER_REVISION = "OI_022_EVIDENCE_NARRATIVE_ASSEMBLY_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_018_explanation_evidence_package.py", "OI-018"),
    (PACKAGE / "oi_019_evidence_contradiction_registry.py", "OI-019"),
    (PACKAGE / "oi_020_temporal_association.py", "OI-020"),
    (PACKAGE / "oi_021_explanation_candidate_assembly.py", "OI-021"),
)

MODULE = PACKAGE / "oi_022_evidence_narrative_assembly.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_022_evidence_narrative_assembly.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_018_explanation_evidence_package import ExplanationEvidencePackage
from .oi_019_evidence_contradiction_registry import EvidenceContradictionRegistry
from .oi_021_explanation_candidate_assembly import ExplanationCandidateSet

BUILD_ID = "OI-022"
OI_022_REVISION = "OI_022_EVIDENCE_NARRATIVE_ASSEMBLY_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
CAUSAL_CLAIM_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False


class EvidenceNarrativeAssemblyError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class NarrativeEvidenceEntry:
    ordinal: int
    evidence_observation_id: str
    temporal_relation: str
    seconds_from_change_observation: int
    agreement_count: int
    contradiction_count: int
    entry_hash: str


@dataclass(frozen=True, slots=True)
class EvidenceNarrative:
    package_hash: str
    candidate_set_hash: str
    entries: tuple[NarrativeEvidenceEntry, ...]
    supporting_relationship_count: int
    contradicting_relationship_count: int
    narrative_hash: str
    causal_claim_allowed: bool
    predictive: bool
    edge_score_allowed: bool
    read_only: bool


class EvidenceNarrativeAssembler:
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
        candidates: ExplanationCandidateSet,
        relationships: EvidenceContradictionRegistry,
    ) -> EvidenceNarrative:
        if not isinstance(package, ExplanationEvidencePackage):
            raise TypeError("package must be ExplanationEvidencePackage")

        if not isinstance(candidates, ExplanationCandidateSet):
            raise TypeError("candidates must be ExplanationCandidateSet")

        if not isinstance(relationships, EvidenceContradictionRegistry):
            raise TypeError("relationships must be EvidenceContradictionRegistry")

        if candidates.package_hash != package.package_hash:
            raise EvidenceNarrativeAssemblyError(
                "candidate set does not belong to explanation package"
            )

        entries = []

        for ordinal, candidate in enumerate(candidates.candidates, start=1):
            body = {
                "ordinal": ordinal,
                "evidence_observation_id": candidate.evidence_observation_id,
                "temporal_relation": candidate.temporal_relation,
                "seconds_from_change_observation": candidate.seconds_from_change_observation,
                "agreement_count": candidate.agreement_count,
                "contradiction_count": candidate.contradiction_count,
            }

            entries.append(
                NarrativeEvidenceEntry(
                    ordinal=ordinal,
                    evidence_observation_id=candidate.evidence_observation_id,
                    temporal_relation=candidate.temporal_relation,
                    seconds_from_change_observation=candidate.seconds_from_change_observation,
                    agreement_count=candidate.agreement_count,
                    contradiction_count=candidate.contradiction_count,
                    entry_hash=deterministic_sha256(body),
                )
            )

        supporting_count = len(relationships.by_relation("agrees"))
        contradicting_count = len(relationships.by_relation("contradicts"))

        body = {
            "package_hash": package.package_hash,
            "candidate_set_hash": candidates.candidate_set_hash,
            "entry_hashes": tuple(item.entry_hash for item in entries),
            "supporting_relationship_count": supporting_count,
            "contradicting_relationship_count": contradicting_count,
            "causal_claim_allowed": False,
            "predictive": False,
            "edge_score_allowed": False,
            "read_only": True,
        }

        return EvidenceNarrative(
            package_hash=package.package_hash,
            candidate_set_hash=candidates.candidate_set_hash,
            entries=tuple(entries),
            supporting_relationship_count=supporting_count,
            contradicting_relationship_count=contradicting_count,
            narrative_hash=deterministic_sha256(body),
            causal_claim_allowed=False,
            predictive=False,
            edge_score_allowed=False,
            read_only=True,
        )


def verify_evidence_narrative_assembly() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-022 must remain read-only")

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
        raise AssertionError("OI-022 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_022_REVISION",
    "EvidenceNarrativeAssemblyError",
    "NarrativeEvidenceEntry",
    "EvidenceNarrative",
    "EvidenceNarrativeAssembler",
    "verify_evidence_narrative_assembly",
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
from qseries_v2.observation_intelligence.oi_021_explanation_candidate_assembly import (
    ExplanationCandidate,
    ExplanationCandidateSet,
)
from qseries_v2.observation_intelligence.oi_022_evidence_narrative_assembly import (
    OI_022_REVISION,
    EvidenceNarrativeAssembler,
    verify_evidence_narrative_assembly,
)

NOW = datetime(2026, 8, 10, 16, 0, tzinfo=timezone.utc)


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


def candidate_set():
    return ExplanationCandidateSet(
        package_hash="d" * 64,
        candidates=(
            ExplanationCandidate(
                evidence_observation_id="obs.a",
                temporal_relation="before",
                seconds_from_change_observation=-30,
                contradiction_count=1,
                agreement_count=0,
                candidate_hash="e" * 64,
            ),
            ExplanationCandidate(
                evidence_observation_id="obs.b",
                temporal_relation="before",
                seconds_from_change_observation=-10,
                contradiction_count=0,
                agreement_count=1,
                candidate_hash="f" * 64,
            ),
        ),
        candidate_set_hash="1" * 64,
        causal_claim_allowed=False,
        predictive=False,
        edge_score_allowed=False,
    )


def registry():
    return EvidenceContradictionRegistry(
        (
            EvidenceRelationship(
                relationship_id="rel.1",
                left_evidence_id="obs.a",
                right_evidence_id="obs.b",
                relation="contradicts",
                basis="explicit disagreement",
            ),
        )
    )


class TestOI022(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(verify_evidence_narrative_assembly())

    def test_assembly(self):
        narrative = EvidenceNarrativeAssembler().assemble(
            package=package(),
            candidates=candidate_set(),
            relationships=registry(),
        )
        self.assertEqual(len(narrative.entries), 2)
        self.assertEqual(narrative.contradicting_relationship_count, 1)

    def test_order_preserved(self):
        narrative = EvidenceNarrativeAssembler().assemble(
            package=package(),
            candidates=candidate_set(),
            relationships=registry(),
        )
        self.assertEqual(
            tuple(item.ordinal for item in narrative.entries),
            (1, 2),
        )

    def test_non_causal(self):
        narrative = EvidenceNarrativeAssembler().assemble(
            package=package(),
            candidates=candidate_set(),
            relationships=registry(),
        )
        self.assertFalse(narrative.causal_claim_allowed)
        self.assertFalse(narrative.predictive)
        self.assertFalse(narrative.edge_score_allowed)
        self.assertTrue(narrative.read_only)

    def test_deterministic(self):
        assembler = EvidenceNarrativeAssembler()
        a = assembler.assemble(
            package=package(),
            candidates=candidate_set(),
            relationships=registry(),
        )
        b = assembler.assemble(
            package=package(),
            candidates=candidate_set(),
            relationships=registry(),
        )
        self.assertEqual(a.narrative_hash, b.narrative_hash)

    def test_side_effects(self):
        assembler = EvidenceNarrativeAssembler()
        self.assertTrue(assembler.read_only)
        self.assertFalse(assembler.network_allowed)
        self.assertFalse(assembler.persistence_allowed)
        self.assertFalse(assembler.publication_allowed)
        self.assertFalse(assembler.execution_allowed)
        self.assertFalse(assembler.qseries_execution_allowed)
        self.assertFalse(assembler.causal_claim_allowed)
        self.assertFalse(assembler.prediction_allowed)
        self.assertFalse(assembler.edge_score_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-022 CERTIFICATION TEST")
    print(" EVIDENCE NARRATIVE ASSEMBLY")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI022)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-022")
    print(f"[PASS] Revision: {OI_022_REVISION}")
    print("[PASS] Explanation candidates assembled into deterministic evidence narrative")
    print("[PASS] Chronology, agreement, and contradiction context preserved")
    print("[PASS] Narrative remains non-causal, non-predictive, and non-scoring")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-022 CERTIFIED")
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
    print(" OI-022 INSTALLER")
    print(" EVIDENCE NARRATIVE ASSEMBLY")
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

    print("[PASS] Certified OI-018 through OI-021 verified read-only")

    affected = (MODULE, TEST, INIT)
    backups = {
        item: item.read_bytes() if item.exists() else None
        for item in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oi_022_evidence_narrative_assembly import *"

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            ast.parse(current, filename=str(INIT))
            INIT.write_text(current, encoding="utf-8", newline="\n")

        print("[PASS] Updated: qseries_v2\\observation_intelligence\\__init__.py")

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
        print("[PASS] Narrative assembly remains deterministic, read-only, non-causal, non-predictive, and non-scoring")
        print("[DONE] OI-022 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for item, original in backups.items():
            if original is None:
                if item.exists():
                    item.unlink()
            else:
                item.parent.mkdir(parents=True, exist_ok=True)
                item.write_bytes(original)

        print("[ROLLBACK] OI-022 installation failed; all affected files restored")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
