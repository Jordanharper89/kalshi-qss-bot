from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-041"
INSTALLER_REVISION = "OI_041_REASONING_EVIDENCE_RELATIONSHIP_REGISTRY_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_040_reasoning_evidence_relationship_projection.py", "OI-040"),
)

MODULE = PACKAGE / "oi_041_reasoning_evidence_relationship_registry.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_041_reasoning_evidence_relationship_registry.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from types import MappingProxyType

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_040_reasoning_evidence_relationship_projection import (
    ReasoningEvidenceRelationship,
    ReasoningEvidenceRelationshipProjection,
)

BUILD_ID = "OI-041"
OI_041_REVISION = "OI_041_REASONING_EVIDENCE_RELATIONSHIP_REGISTRY_V1"

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


class ReasoningEvidenceRelationshipRegistryError(ValueError):
    pass


class ReasoningEvidenceRelationshipRegistry:
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

    def __init__(
        self,
        projection: ReasoningEvidenceRelationshipProjection,
    ) -> None:
        if not isinstance(
            projection,
            ReasoningEvidenceRelationshipProjection,
        ):
            raise TypeError(
                "projection must be ReasoningEvidenceRelationshipProjection"
            )

        keys = tuple(
            (
                item.left_observation_id,
                item.right_observation_id,
            )
            for item in projection.relationships
        )

        if len(keys) != len(set(keys)):
            raise ReasoningEvidenceRelationshipRegistryError(
                "duplicate evidence relationship pair"
            )

        self._projection = projection
        self._relationships = tuple(
            projection.relationships
        )

    @property
    def relationships(
        self,
    ) -> tuple[ReasoningEvidenceRelationship, ...]:
        return self._relationships

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(
            {
                "projection_hash": (
                    self._projection.projection_hash
                ),
                "relationship_hashes": tuple(
                    item.relationship_hash
                    for item in self._relationships
                ),
            }
        )

    def by_observation(
        self,
        canonical_observation_id: str,
    ) -> tuple[ReasoningEvidenceRelationship, ...]:
        key = str(canonical_observation_id).strip()

        return tuple(
            item
            for item in self._relationships
            if (
                item.left_observation_id == key
                or item.right_observation_id == key
            )
        )

    def by_relation(
        self,
        relation_type: str,
    ) -> tuple[ReasoningEvidenceRelationship, ...]:
        key = " ".join(
            str(relation_type).strip().lower().split()
        )

        return tuple(
            item
            for item in self._relationships
            if key in item.relation_types
        )

    def by_shared_context_role(
        self,
        role: str,
    ) -> tuple[ReasoningEvidenceRelationship, ...]:
        key = " ".join(
            str(role).strip().lower().split()
        )

        return tuple(
            item
            for item in self._relationships
            if key in item.shared_context_roles
        )


def verify_reasoning_evidence_relationship_registry() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-041 must remain read-only"
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
            "OI-041 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_041_REVISION",
    "ReasoningEvidenceRelationshipRegistryError",
    "ReasoningEvidenceRelationshipRegistry",
    "verify_reasoning_evidence_relationship_registry",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_040_reasoning_evidence_relationship_projection import (
    ReasoningEvidenceRelationship,
    ReasoningEvidenceRelationshipProjection,
)
from qseries_v2.observation_intelligence.oi_041_reasoning_evidence_relationship_registry import (
    OI_041_REVISION,
    ReasoningEvidenceRelationshipRegistry,
    verify_reasoning_evidence_relationship_registry,
)


def projection():
    return ReasoningEvidenceRelationshipProjection(
        evidence_registry_hash="a" * 64,
        context_registry_hash="b" * 64,
        relationships=(
            ReasoningEvidenceRelationship(
                left_observation_id="obs.1",
                right_observation_id="obs.2",
                relation_types=(
                    "same_subject",
                    "shared_context_role",
                ),
                shared_context_roles=(
                    "evidence",
                    "source_context",
                ),
                relationship_hash="c" * 64,
            ),
        ),
        relationship_count=1,
        projection_hash="d" * 64,
        read_only=True,
    )


class TestOI041(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_reasoning_evidence_relationship_registry()
        )

    def test_registry(self):
        registry = ReasoningEvidenceRelationshipRegistry(
            projection()
        )

        self.assertEqual(
            len(registry.relationships),
            1,
        )

    def test_observation_query(self):
        registry = ReasoningEvidenceRelationshipRegistry(
            projection()
        )

        self.assertEqual(
            len(
                registry.by_observation(
                    "obs.1"
                )
            ),
            1,
        )

    def test_relation_query(self):
        registry = ReasoningEvidenceRelationshipRegistry(
            projection()
        )

        self.assertEqual(
            len(
                registry.by_relation(
                    "same_subject"
                )
            ),
            1,
        )

    def test_context_role_query(self):
        registry = ReasoningEvidenceRelationshipRegistry(
            projection()
        )

        self.assertEqual(
            len(
                registry.by_shared_context_role(
                    "evidence"
                )
            ),
            1,
        )

    def test_unknown(self):
        registry = ReasoningEvidenceRelationshipRegistry(
            projection()
        )

        self.assertEqual(
            registry.by_observation(
                "obs.unknown"
            ),
            (),
        )

    def test_deterministic(self):
        a = ReasoningEvidenceRelationshipRegistry(
            projection()
        )

        b = ReasoningEvidenceRelationshipRegistry(
            projection()
        )

        self.assertEqual(
            a.registry_hash,
            b.registry_hash,
        )

    def test_side_effects(self):
        registry = ReasoningEvidenceRelationshipRegistry(
            projection()
        )

        self.assertTrue(registry.read_only)
        self.assertFalse(registry.network_allowed)
        self.assertFalse(registry.persistence_allowed)
        self.assertFalse(registry.publication_allowed)
        self.assertFalse(registry.execution_allowed)
        self.assertFalse(registry.qseries_execution_allowed)
        self.assertFalse(registry.prediction_allowed)
        self.assertFalse(registry.edge_score_allowed)
        self.assertFalse(registry.probability_allowed)
        self.assertFalse(registry.causal_claim_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-041 CERTIFICATION TEST")
    print(" REASONING EVIDENCE RELATIONSHIP REGISTRY")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI041
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-041")
    print(f"[PASS] Revision: {OI_041_REVISION}")
    print("[PASS] Structural evidence relationship registry certified")
    print("[PASS] Reverse queries by observation, relationship type, and shared context role certified")
    print("[PASS] Registry remains deterministic, read-only, structural, and non-causal")
    print("[PASS] Network, persistence, publication, prediction, scoring, and execution disabled")
    print("[DONE] OI-041 CERTIFIED")
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
    print(" OI-041 INSTALLER")
    print(" REASONING EVIDENCE RELATIONSHIP REGISTRY")
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
        "[PASS] Certified OI-040 verified read-only"
    )

    affected = (MODULE, TEST, INIT)
    backups = {
        item: item.read_bytes() if item.exists() else None
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
            "from .oi_041_reasoning_evidence_relationship_registry import *"
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
            "[PASS] Relationship registry remains deterministic, "
            "read-only, structural, and non-causal"
        )
        print("[DONE] OI-041 INSTALLATION COMPLETE")
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
            "[ROLLBACK] OI-041 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
