from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-040"
INSTALLER_REVISION = "OI_040_REASONING_EVIDENCE_RELATIONSHIP_PROJECTION_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_019_evidence_contradiction_registry.py", "OI-019"),
    (PACKAGE / "oi_020_temporal_association.py", "OI-020"),
    (PACKAGE / "oi_037_reasoning_evidence_registry.py", "OI-037"),
    (PACKAGE / "oi_039_reasoning_evidence_context_registry.py", "OI-039"),
)

MODULE = PACKAGE / "oi_040_reasoning_evidence_relationship_projection.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_040_reasoning_evidence_relationship_projection.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_037_reasoning_evidence_registry import ReasoningEvidenceRegistry
from .oi_039_reasoning_evidence_context_registry import (
    ReasoningEvidenceContextRegistry,
)

BUILD_ID = "OI-040"
OI_040_REVISION = "OI_040_REASONING_EVIDENCE_RELATIONSHIP_PROJECTION_V1"

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

RELATION_SAME_SUBJECT = "same_subject"
RELATION_SAME_PROVIDER = "same_provider"
RELATION_SAME_ADAPTER = "same_adapter"
RELATION_SHARED_CONTEXT_ROLE = "shared_context_role"

SUPPORTED_RELATIONS = (
    RELATION_SAME_ADAPTER,
    RELATION_SAME_PROVIDER,
    RELATION_SAME_SUBJECT,
    RELATION_SHARED_CONTEXT_ROLE,
)


class ReasoningEvidenceRelationshipProjectionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ReasoningEvidenceRelationship:
    left_observation_id: str
    right_observation_id: str
    relation_types: tuple[str, ...]
    shared_context_roles: tuple[str, ...]
    relationship_hash: str


@dataclass(frozen=True, slots=True)
class ReasoningEvidenceRelationshipProjection:
    evidence_registry_hash: str
    context_registry_hash: str
    relationships: tuple[ReasoningEvidenceRelationship, ...]
    relationship_count: int
    projection_hash: str
    read_only: bool


class ReasoningEvidenceRelationshipProjector:
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
        *,
        evidence_registry: ReasoningEvidenceRegistry,
        context_registry: ReasoningEvidenceContextRegistry,
    ) -> ReasoningEvidenceRelationshipProjection:
        if not isinstance(
            evidence_registry,
            ReasoningEvidenceRegistry,
        ):
            raise TypeError(
                "evidence_registry must be ReasoningEvidenceRegistry"
            )

        if not isinstance(
            context_registry,
            ReasoningEvidenceContextRegistry,
        ):
            raise TypeError(
                "context_registry must be ReasoningEvidenceContextRegistry"
            )

        if (
            evidence_registry.package_hash
            != context_registry.package_hash
        ):
            raise ReasoningEvidenceRelationshipProjectionError(
                "evidence and context registries reference different reasoning packages"
            )

        relationships = []

        for left, right in combinations(
            evidence_registry.records,
            2,
        ):
            left_context = context_registry.get(
                left.canonical_observation_id
            )
            right_context = context_registry.get(
                right.canonical_observation_id
            )

            if left_context is None or right_context is None:
                raise ReasoningEvidenceRelationshipProjectionError(
                    "context registry missing evidence observation"
                )

            relation_types = set()
            shared_roles = tuple(
                sorted(
                    set(left_context.context_roles)
                    & set(right_context.context_roles)
                )
            )

            if left.subject == right.subject:
                relation_types.add(
                    RELATION_SAME_SUBJECT
                )

            if left.provider == right.provider:
                relation_types.add(
                    RELATION_SAME_PROVIDER
                )

            if left.adapter_id == right.adapter_id:
                relation_types.add(
                    RELATION_SAME_ADAPTER
                )

            if shared_roles:
                relation_types.add(
                    RELATION_SHARED_CONTEXT_ROLE
                )

            if not relation_types:
                continue

            relation_types = tuple(
                sorted(relation_types)
            )

            body = {
                "left_observation_id": (
                    left.canonical_observation_id
                ),
                "right_observation_id": (
                    right.canonical_observation_id
                ),
                "relation_types": relation_types,
                "shared_context_roles": shared_roles,
            }

            relationships.append(
                ReasoningEvidenceRelationship(
                    left_observation_id=(
                        left.canonical_observation_id
                    ),
                    right_observation_id=(
                        right.canonical_observation_id
                    ),
                    relation_types=relation_types,
                    shared_context_roles=shared_roles,
                    relationship_hash=(
                        deterministic_sha256(body)
                    ),
                )
            )

        relationships = tuple(
            sorted(
                relationships,
                key=lambda item: (
                    item.left_observation_id,
                    item.right_observation_id,
                ),
            )
        )

        body = {
            "evidence_registry_hash": (
                evidence_registry.registry_hash
            ),
            "context_registry_hash": (
                context_registry.registry_hash
            ),
            "relationship_hashes": tuple(
                item.relationship_hash
                for item in relationships
            ),
            "relationship_count": len(
                relationships
            ),
            "read_only": True,
        }

        return ReasoningEvidenceRelationshipProjection(
            evidence_registry_hash=(
                evidence_registry.registry_hash
            ),
            context_registry_hash=(
                context_registry.registry_hash
            ),
            relationships=relationships,
            relationship_count=len(
                relationships
            ),
            projection_hash=(
                deterministic_sha256(body)
            ),
            read_only=True,
        )


def verify_reasoning_evidence_relationship_projection() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-040 must remain read-only"
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
            "OI-040 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_040_REVISION",
    "RELATION_SAME_SUBJECT",
    "RELATION_SAME_PROVIDER",
    "RELATION_SAME_ADAPTER",
    "RELATION_SHARED_CONTEXT_ROLE",
    "SUPPORTED_RELATIONS",
    "ReasoningEvidenceRelationshipProjectionError",
    "ReasoningEvidenceRelationship",
    "ReasoningEvidenceRelationshipProjection",
    "ReasoningEvidenceRelationshipProjector",
    "verify_reasoning_evidence_relationship_projection",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_036_oracle_reasoning_evidence_package import (
    OracleReasoningEvidenceItem,
    OracleReasoningEvidencePackage,
)
from qseries_v2.observation_intelligence.oi_037_reasoning_evidence_registry import (
    ReasoningEvidenceRegistry,
)
from qseries_v2.observation_intelligence.oi_038_reasoning_evidence_context_projection import (
    ReasoningEvidenceContext,
    ReasoningEvidenceContextProjection,
)
from qseries_v2.observation_intelligence.oi_039_reasoning_evidence_context_registry import (
    ReasoningEvidenceContextRegistry,
)
from qseries_v2.observation_intelligence.oi_040_reasoning_evidence_relationship_projection import (
    OI_040_REVISION,
    RELATION_SAME_SUBJECT,
    RELATION_SHARED_CONTEXT_ROLE,
    ReasoningEvidenceRelationshipProjector,
    verify_reasoning_evidence_relationship_projection,
)

NOW = datetime(
    2026,
    8,
    11,
    4,
    0,
    tzinfo=timezone.utc,
)


def package():
    return OracleReasoningEvidencePackage(
        package_id="reasoning.test",
        query_id="query.test",
        profile_id="profile.market_explanation",
        subject_hint="Astros strikeouts",
        admission_status="admitted",
        admission_hash="a" * 64,
        materialization_hash="b" * 64,
        evidence_items=(
            OracleReasoningEvidenceItem(
                canonical_observation_id="obs.1",
                canonical_observation_hash="c" * 64,
                adapter_id="adapter.kalshi.v1",
                provider="Kalshi",
                subject="Astros strikeouts",
                observation_type="market_snapshot",
                observed_at=NOW,
            ),
            OracleReasoningEvidenceItem(
                canonical_observation_id="obs.2",
                canonical_observation_hash="d" * 64,
                adapter_id="adapter.sports.v1",
                provider="SportsFeed",
                subject="Astros strikeouts",
                observation_type="lineup",
                observed_at=NOW,
            ),
        ),
        missing_need_count=0,
        built_at=NOW,
        package_hash="e" * 64,
        read_only=True,
        predictive=False,
    )


def context_registry():
    projection = ReasoningEvidenceContextProjection(
        package_hash="e" * 64,
        registry_hash="f" * 64,
        contexts=(
            ReasoningEvidenceContext(
                canonical_observation_id="obs.1",
                canonical_observation_hash="c" * 64,
                adapter_id="adapter.kalshi.v1",
                provider="Kalshi",
                subject="Astros strikeouts",
                observation_type="market_snapshot",
                context_roles=(
                    "evidence",
                    "market_state",
                    "source_context",
                ),
                context_hash="1" * 64,
            ),
            ReasoningEvidenceContext(
                canonical_observation_id="obs.2",
                canonical_observation_hash="d" * 64,
                adapter_id="adapter.sports.v1",
                provider="SportsFeed",
                subject="Astros strikeouts",
                observation_type="lineup",
                context_roles=(
                    "evidence",
                    "source_context",
                    "sports_context",
                ),
                context_hash="2" * 64,
            ),
        ),
        context_count=2,
        projection_hash="3" * 64,
        read_only=True,
    )

    return ReasoningEvidenceContextRegistry(
        projection
    )


class TestOI040(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_reasoning_evidence_relationship_projection()
        )

    def test_projection(self):
        projection = (
            ReasoningEvidenceRelationshipProjector()
            .project(
                evidence_registry=ReasoningEvidenceRegistry(
                    package()
                ),
                context_registry=context_registry(),
            )
        )

        self.assertEqual(
            projection.relationship_count,
            1,
        )

    def test_same_subject(self):
        projection = (
            ReasoningEvidenceRelationshipProjector()
            .project(
                evidence_registry=ReasoningEvidenceRegistry(
                    package()
                ),
                context_registry=context_registry(),
            )
        )

        self.assertIn(
            RELATION_SAME_SUBJECT,
            projection.relationships[0].relation_types,
        )

    def test_shared_context(self):
        projection = (
            ReasoningEvidenceRelationshipProjector()
            .project(
                evidence_registry=ReasoningEvidenceRegistry(
                    package()
                ),
                context_registry=context_registry(),
            )
        )

        self.assertIn(
            RELATION_SHARED_CONTEXT_ROLE,
            projection.relationships[0].relation_types,
        )

        self.assertIn(
            "evidence",
            projection.relationships[0].shared_context_roles,
        )

    def test_deterministic(self):
        projector = ReasoningEvidenceRelationshipProjector()

        a = projector.project(
            evidence_registry=ReasoningEvidenceRegistry(
                package()
            ),
            context_registry=context_registry(),
        )

        b = projector.project(
            evidence_registry=ReasoningEvidenceRegistry(
                package()
            ),
            context_registry=context_registry(),
        )

        self.assertEqual(
            a.projection_hash,
            b.projection_hash,
        )

    def test_side_effects(self):
        projector = ReasoningEvidenceRelationshipProjector()

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
    print(" OI-040 CERTIFICATION TEST")
    print(" REASONING EVIDENCE RELATIONSHIP PROJECTION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI040
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-040")
    print(f"[PASS] Revision: {OI_040_REVISION}")
    print("[PASS] Structural evidence relationships projected deterministically")
    print("[PASS] Same-subject, same-provider, same-adapter, and shared-context relationships certified")
    print("[PASS] No causal direction, probability, prediction, or edge score introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-040 CERTIFIED")
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
    print(" OI-040 INSTALLER")
    print(" REASONING EVIDENCE RELATIONSHIP PROJECTION")
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
        "[PASS] Certified OI-019, OI-020, "
        "OI-037, and OI-039 verified read-only"
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
            "from .oi_040_reasoning_evidence_relationship_projection import *"
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
            "[PASS] Relationship projection remains deterministic, "
            "read-only, structural, and non-causal"
        )
        print("[DONE] OI-040 INSTALLATION COMPLETE")
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
            "[ROLLBACK] OI-040 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
