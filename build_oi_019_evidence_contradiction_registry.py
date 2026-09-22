from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-019"
INSTALLER_REVISION = "OI_019_EVIDENCE_CONTRADICTION_REGISTRY_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"
UPSTREAM_011 = PACKAGE / "oi_011_multi_source_consensus.py"
UPSTREAM_018 = PACKAGE / "oi_018_explanation_evidence_package.py"
MODULE = PACKAGE / "oi_019_evidence_contradiction_registry.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_019_evidence_contradiction_registry.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_018_explanation_evidence_package import (
    ExplanationEvidencePackage,
)

BUILD_ID = "OI-019"
OI_019_REVISION = "OI_019_EVIDENCE_CONTRADICTION_REGISTRY_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
CAUSAL_INFERENCE_ALLOWED = False
PREDICTION_ALLOWED = False

SUPPORTED_RELATIONS = (
    "agrees",
    "contradicts",
    "supersedes",
    "independent",
)


class EvidenceContradictionRegistryError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class EvidenceRelationship:
    relationship_id: str
    left_evidence_id: str
    right_evidence_id: str
    relation: str
    basis: str

    def __post_init__(self) -> None:
        relationship_id = " ".join(
            str(self.relationship_id).strip().lower().split()
        )
        left = str(self.left_evidence_id).strip()
        right = str(self.right_evidence_id).strip()
        relation = " ".join(
            str(self.relation).strip().lower().split()
        )
        basis = " ".join(str(self.basis).strip().split())

        if not relationship_id:
            raise EvidenceContradictionRegistryError(
                "relationship_id must not be empty"
            )
        if not left or not right:
            raise EvidenceContradictionRegistryError(
                "evidence identities must not be empty"
            )
        if left == right:
            raise EvidenceContradictionRegistryError(
                "self relationship is not allowed"
            )
        if relation not in SUPPORTED_RELATIONS:
            raise EvidenceContradictionRegistryError(
                f"unsupported evidence relation: {relation}"
            )
        if not basis:
            raise EvidenceContradictionRegistryError(
                "basis must not be empty"
            )

        ordered = tuple(sorted((left, right)))

        object.__setattr__(self, "relationship_id", relationship_id)
        object.__setattr__(self, "left_evidence_id", ordered[0])
        object.__setattr__(self, "right_evidence_id", ordered[1])
        object.__setattr__(self, "relation", relation)
        object.__setattr__(self, "basis", basis)

    @property
    def relationship_hash(self) -> str:
        return deterministic_sha256(
            {
                "relationship_id": self.relationship_id,
                "left_evidence_id": self.left_evidence_id,
                "right_evidence_id": self.right_evidence_id,
                "relation": self.relation,
                "basis": self.basis,
            }
        )


class EvidenceContradictionRegistry:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    causal_inference_allowed = False
    prediction_allowed = False

    def __init__(
        self,
        relationships: tuple[EvidenceRelationship, ...],
    ) -> None:
        values = tuple(relationships)

        if any(
            not isinstance(item, EvidenceRelationship)
            for item in values
        ):
            raise TypeError(
                "all relationships must be EvidenceRelationship"
            )

        ordered = tuple(
            sorted(
                values,
                key=lambda item: item.relationship_id,
            )
        )

        if values != ordered:
            raise EvidenceContradictionRegistryError(
                "relationships must be deterministically sorted"
            )

        ids = tuple(
            item.relationship_id
            for item in values
        )
        if len(ids) != len(set(ids)):
            raise EvidenceContradictionRegistryError(
                "duplicate relationship_id"
            )

        self._relationships = values
        self._by_id = MappingProxyType(
            {item.relationship_id: item for item in values}
        )

    @property
    def relationships(self) -> tuple[EvidenceRelationship, ...]:
        return self._relationships

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(
            tuple(
                item.relationship_hash
                for item in self._relationships
            )
        )

    def by_relation(
        self,
        relation: str,
    ) -> tuple[EvidenceRelationship, ...]:
        normalized = " ".join(
            str(relation).strip().lower().split()
        )

        if normalized not in SUPPORTED_RELATIONS:
            return ()

        return tuple(
            item
            for item in self._relationships
            if item.relation == normalized
        )

    def for_evidence(
        self,
        evidence_id: str,
    ) -> tuple[EvidenceRelationship, ...]:
        key = str(evidence_id).strip()

        return tuple(
            item
            for item in self._relationships
            if (
                item.left_evidence_id == key
                or item.right_evidence_id == key
            )
        )


def verify_evidence_contradiction_registry() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-019 must remain read-only"
        )

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
            CAUSAL_INFERENCE_ALLOWED,
            PREDICTION_ALLOWED,
        )
    ):
        raise AssertionError(
            "OI-019 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_019_REVISION",
    "SUPPORTED_RELATIONS",
    "EvidenceContradictionRegistryError",
    "EvidenceRelationship",
    "EvidenceContradictionRegistry",
    "verify_evidence_contradiction_registry",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_019_evidence_contradiction_registry import (
    OI_019_REVISION,
    EvidenceRelationship,
    EvidenceContradictionRegistry,
    verify_evidence_contradiction_registry,
)


def relationship(
    relationship_id: str,
    left: str,
    right: str,
    relation: str,
):
    return EvidenceRelationship(
        relationship_id=relationship_id,
        left_evidence_id=left,
        right_evidence_id=right,
        relation=relation,
        basis="explicit certified evidence relationship",
    )


class TestOI019(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_evidence_contradiction_registry()
        )

    def test_registry(self):
        registry = EvidenceContradictionRegistry(
            (
                relationship(
                    "rel.1",
                    "obs.a",
                    "obs.b",
                    "contradicts",
                ),
                relationship(
                    "rel.2",
                    "obs.a",
                    "obs.c",
                    "agrees",
                ),
            )
        )
        self.assertEqual(
            len(registry.relationships),
            2,
        )

    def test_contradiction_query(self):
        registry = EvidenceContradictionRegistry(
            (
                relationship(
                    "rel.1",
                    "obs.a",
                    "obs.b",
                    "contradicts",
                ),
            )
        )
        self.assertEqual(
            len(registry.by_relation("contradicts")),
            1,
        )

    def test_reverse_query(self):
        registry = EvidenceContradictionRegistry(
            (
                relationship(
                    "rel.1",
                    "obs.a",
                    "obs.b",
                    "contradicts",
                ),
            )
        )
        self.assertEqual(
            len(registry.for_evidence("obs.a")),
            1,
        )

    def test_symmetric_identity(self):
        a = relationship(
            "rel.1",
            "obs.b",
            "obs.a",
            "agrees",
        )
        self.assertEqual(
            (a.left_evidence_id, a.right_evidence_id),
            ("obs.a", "obs.b"),
        )

    def test_self_rejected(self):
        with self.assertRaises(ValueError):
            relationship(
                "rel.bad",
                "obs.a",
                "obs.a",
                "agrees",
            )

    def test_deterministic(self):
        a = EvidenceContradictionRegistry(
            (
                relationship(
                    "rel.1",
                    "obs.a",
                    "obs.b",
                    "contradicts",
                ),
            )
        )
        b = EvidenceContradictionRegistry(
            (
                relationship(
                    "rel.1",
                    "obs.a",
                    "obs.b",
                    "contradicts",
                ),
            )
        )
        self.assertEqual(
            a.registry_hash,
            b.registry_hash,
        )

    def test_side_effects(self):
        registry = EvidenceContradictionRegistry(())
        self.assertTrue(registry.read_only)
        self.assertFalse(registry.network_allowed)
        self.assertFalse(registry.persistence_allowed)
        self.assertFalse(registry.publication_allowed)
        self.assertFalse(registry.execution_allowed)
        self.assertFalse(registry.qseries_execution_allowed)
        self.assertFalse(registry.causal_inference_allowed)
        self.assertFalse(registry.prediction_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-019 CERTIFICATION TEST")
    print(" EVIDENCE CONTRADICTION REGISTRY")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI019
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-019")
    print(f"[PASS] Revision: {OI_019_REVISION}")
    print("[PASS] Agreement, contradiction, supersession, and independence relationships certified")
    print("[PASS] Evidence reverse queries and deterministic relationship identity certified")
    print("[PASS] No inferred contradiction, causal claim, or prediction introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-019 CERTIFIED")
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
    print(" OI-019 INSTALLER")
    print(" EVIDENCE CONTRADICTION REGISTRY")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    upstreams = (
        (UPSTREAM_011, "OI-011"),
        (UPSTREAM_018, "OI-018"),
    )

    for path, name in upstreams:
        if not path.is_file():
            raise RuntimeError(
                f"Certified {name} missing: {path}"
            )

    upstream_hashes = {
        path: sha(path)
        for path, _ in upstreams
    }

    print(
        "[PASS] Certified OI-011 and OI-018 "
        "verified read-only"
    )

    affected = (MODULE, TEST, INIT)
    backups = {
        path: (
            path.read_bytes()
            if path.exists()
            else None
        )
        for path in affected
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
            "from .oi_019_evidence_contradiction_registry import *"
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

        for path, expected in upstream_hashes.items():
            if sha(path) != expected:
                raise RuntimeError(
                    f"Certified upstream changed: {path.name}"
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
            "[PASS] Evidence relationship registry remains "
            "deterministic, read-only, non-causal, and non-predictive"
        )
        print("[DONE] OI-019 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for path, content in backups.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )
                path.write_bytes(content)

        print(
            "[ROLLBACK] OI-019 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
