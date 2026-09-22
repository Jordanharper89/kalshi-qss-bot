from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-043"
INSTALLER_REVISION = "OI_043_STRUCTURAL_REASONING_SYNTHESIS_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_039_reasoning_evidence_context_registry.py", "OI-039"),
    (PACKAGE / "oi_041_reasoning_evidence_relationship_registry.py", "OI-041"),
    (PACKAGE / "oi_042_oracle_reasoning_assembly.py", "OI-042"),
)

MODULE = PACKAGE / "oi_043_structural_reasoning_synthesis.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_043_structural_reasoning_synthesis.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_039_reasoning_evidence_context_registry import (
    ReasoningEvidenceContextRegistry,
)
from .oi_041_reasoning_evidence_relationship_registry import (
    ReasoningEvidenceRelationshipRegistry,
)
from .oi_042_oracle_reasoning_assembly import OracleReasoningAssembly

BUILD_ID = "OI-043"
OI_043_REVISION = "OI_043_STRUCTURAL_REASONING_SYNTHESIS_V1"

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


class StructuralReasoningSynthesisError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class StructuralReasoningSignal:
    signal_type: str
    subject: str
    evidence_observation_ids: tuple[str, ...]
    context_roles: tuple[str, ...]
    relationship_types: tuple[str, ...]
    signal_hash: str


@dataclass(frozen=True, slots=True)
class StructuralReasoningSynthesis:
    assembly_hash: str
    signals: tuple[StructuralReasoningSignal, ...]
    signal_count: int
    synthesis_hash: str
    read_only: bool
    predictive: bool
    causal_claim_allowed: bool


class StructuralReasoningSynthesizer:
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

    def synthesize(
        self,
        *,
        assembly: OracleReasoningAssembly,
        context_registry: ReasoningEvidenceContextRegistry,
        relationship_registry: ReasoningEvidenceRelationshipRegistry,
    ) -> StructuralReasoningSynthesis:
        if not isinstance(assembly, OracleReasoningAssembly):
            raise TypeError("assembly must be OracleReasoningAssembly")
        if not isinstance(
            context_registry,
            ReasoningEvidenceContextRegistry,
        ):
            raise TypeError(
                "context_registry must be ReasoningEvidenceContextRegistry"
            )
        if not isinstance(
            relationship_registry,
            ReasoningEvidenceRelationshipRegistry,
        ):
            raise TypeError(
                "relationship_registry must be ReasoningEvidenceRelationshipRegistry"
            )

        if assembly.context_registry_hash != context_registry.registry_hash:
            raise StructuralReasoningSynthesisError(
                "assembly/context registry lineage mismatch"
            )

        if (
            assembly.relationship_registry_hash
            != relationship_registry.registry_hash
        ):
            raise StructuralReasoningSynthesisError(
                "assembly/relationship registry lineage mismatch"
            )

        subjects = sorted(
            {
                item.subject
                for item in context_registry.contexts
            }
        )

        signals = []

        for subject in subjects:
            subject_contexts = tuple(
                item
                for item in context_registry.contexts
                if item.subject == subject
            )

            ids = tuple(
                sorted(
                    item.canonical_observation_id
                    for item in subject_contexts
                )
            )

            roles = tuple(
                sorted(
                    {
                        role
                        for item in subject_contexts
                        for role in item.context_roles
                    }
                )
            )

            relationship_types = tuple(
                sorted(
                    {
                        relation
                        for relationship in relationship_registry.relationships
                        if (
                            relationship.left_observation_id in ids
                            or relationship.right_observation_id in ids
                        )
                        for relation in relationship.relation_types
                    }
                )
            )

            signal_type = (
                "multi_evidence_context"
                if len(ids) > 1
                else "single_evidence_context"
            )

            body = {
                "signal_type": signal_type,
                "subject": subject,
                "evidence_observation_ids": ids,
                "context_roles": roles,
                "relationship_types": relationship_types,
            }

            signals.append(
                StructuralReasoningSignal(
                    signal_type=signal_type,
                    subject=subject,
                    evidence_observation_ids=ids,
                    context_roles=roles,
                    relationship_types=relationship_types,
                    signal_hash=deterministic_sha256(body),
                )
            )

        signals = tuple(
            sorted(
                signals,
                key=lambda item: (
                    item.subject,
                    item.signal_type,
                ),
            )
        )

        body = {
            "assembly_hash": assembly.assembly_hash,
            "signal_hashes": tuple(
                item.signal_hash
                for item in signals
            ),
            "signal_count": len(signals),
            "read_only": True,
            "predictive": False,
            "causal_claim_allowed": False,
        }

        return StructuralReasoningSynthesis(
            assembly_hash=assembly.assembly_hash,
            signals=signals,
            signal_count=len(signals),
            synthesis_hash=deterministic_sha256(body),
            read_only=True,
            predictive=False,
            causal_claim_allowed=False,
        )


def verify_structural_reasoning_synthesis() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-043 must remain read-only")

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
        raise AssertionError("OI-043 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_043_REVISION",
    "StructuralReasoningSynthesisError",
    "StructuralReasoningSignal",
    "StructuralReasoningSynthesis",
    "StructuralReasoningSynthesizer",
    "verify_structural_reasoning_synthesis",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_038_reasoning_evidence_context_projection import (
    ReasoningEvidenceContext,
    ReasoningEvidenceContextProjection,
)
from qseries_v2.observation_intelligence.oi_039_reasoning_evidence_context_registry import (
    ReasoningEvidenceContextRegistry,
)
from qseries_v2.observation_intelligence.oi_040_reasoning_evidence_relationship_projection import (
    ReasoningEvidenceRelationship,
    ReasoningEvidenceRelationshipProjection,
)
from qseries_v2.observation_intelligence.oi_041_reasoning_evidence_relationship_registry import (
    ReasoningEvidenceRelationshipRegistry,
)
from qseries_v2.observation_intelligence.oi_042_oracle_reasoning_assembly import (
    OracleReasoningAssembly,
)
from qseries_v2.observation_intelligence.oi_043_structural_reasoning_synthesis import (
    OI_043_REVISION,
    StructuralReasoningSynthesizer,
    verify_structural_reasoning_synthesis,
)

NOW = datetime(2026, 8, 11, 6, 0, tzinfo=timezone.utc)


def context_registry():
    return ReasoningEvidenceContextRegistry(
        ReasoningEvidenceContextProjection(
            package_hash="a" * 64,
            registry_hash="b" * 64,
            contexts=(
                ReasoningEvidenceContext(
                    canonical_observation_id="obs.1",
                    canonical_observation_hash="c" * 64,
                    adapter_id="adapter.kalshi.v1",
                    provider="Kalshi",
                    subject="Astros strikeouts",
                    observation_type="market_snapshot",
                    context_roles=("evidence", "market_state"),
                    context_hash="d" * 64,
                ),
                ReasoningEvidenceContext(
                    canonical_observation_id="obs.2",
                    canonical_observation_hash="e" * 64,
                    adapter_id="adapter.sports.v1",
                    provider="SportsFeed",
                    subject="Astros strikeouts",
                    observation_type="lineup",
                    context_roles=("evidence", "sports_context"),
                    context_hash="f" * 64,
                ),
            ),
            context_count=2,
            projection_hash="1" * 64,
            read_only=True,
        )
    )


def relationship_registry():
    return ReasoningEvidenceRelationshipRegistry(
        ReasoningEvidenceRelationshipProjection(
            evidence_registry_hash="2" * 64,
            context_registry_hash="3" * 64,
            relationships=(
                ReasoningEvidenceRelationship(
                    left_observation_id="obs.1",
                    right_observation_id="obs.2",
                    relation_types=("same_subject", "shared_context_role"),
                    shared_context_roles=("evidence",),
                    relationship_hash="4" * 64,
                ),
            ),
            relationship_count=1,
            projection_hash="5" * 64,
            read_only=True,
        )
    )


def assembly():
    context = context_registry()
    relationships = relationship_registry()

    return OracleReasoningAssembly(
        assembly_id="assembly.test",
        query_id="query.test",
        profile_id="profile.market_explanation",
        subject_hint="Astros strikeouts",
        admission_status="admitted",
        evidence_package_hash="6" * 64,
        context_registry_hash=context.registry_hash,
        relationship_registry_hash=relationships.registry_hash,
        evidence_count=2,
        context_count=2,
        relationship_count=1,
        missing_need_count=0,
        assembled_at=NOW,
        assembly_hash="7" * 64,
        read_only=True,
        predictive=False,
        causal_claim_allowed=False,
    )


class TestOI043(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_structural_reasoning_synthesis()
        )

    def test_synthesis(self):
        result = StructuralReasoningSynthesizer().synthesize(
            assembly=assembly(),
            context_registry=context_registry(),
            relationship_registry=relationship_registry(),
        )

        self.assertEqual(result.signal_count, 1)
        self.assertEqual(
            result.signals[0].signal_type,
            "multi_evidence_context",
        )

    def test_roles_preserved(self):
        result = StructuralReasoningSynthesizer().synthesize(
            assembly=assembly(),
            context_registry=context_registry(),
            relationship_registry=relationship_registry(),
        )

        self.assertIn(
            "market_state",
            result.signals[0].context_roles,
        )
        self.assertIn(
            "sports_context",
            result.signals[0].context_roles,
        )

    def test_relationships_preserved(self):
        result = StructuralReasoningSynthesizer().synthesize(
            assembly=assembly(),
            context_registry=context_registry(),
            relationship_registry=relationship_registry(),
        )

        self.assertIn(
            "same_subject",
            result.signals[0].relationship_types,
        )

    def test_deterministic(self):
        synthesizer = StructuralReasoningSynthesizer()

        a = synthesizer.synthesize(
            assembly=assembly(),
            context_registry=context_registry(),
            relationship_registry=relationship_registry(),
        )
        b = synthesizer.synthesize(
            assembly=assembly(),
            context_registry=context_registry(),
            relationship_registry=relationship_registry(),
        )

        self.assertEqual(
            a.synthesis_hash,
            b.synthesis_hash,
        )

    def test_side_effects(self):
        item = StructuralReasoningSynthesizer()

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


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-043 CERTIFICATION TEST")
    print(" STRUCTURAL REASONING SYNTHESIS")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI043
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-043")
    print(f"[PASS] Revision: {OI_043_REVISION}")
    print("[PASS] Evidence, context roles, and structural relationships synthesized by subject")
    print("[PASS] Multi-evidence versus single-evidence structural context certified")
    print("[PASS] No causal claim, probability, prediction, or edge score introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-043 CERTIFIED")
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
    print(" OI-043 INSTALLER")
    print(" STRUCTURAL REASONING SYNTHESIS")
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

    print(
        "[PASS] Certified OI-039, OI-041, "
        "and OI-042 verified read-only"
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
        export = "from .oi_043_structural_reasoning_synthesis import *"

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

        print(f"[PASS] Deterministic install hash: {install_hash}")
        print(
            "[PASS] Structural synthesis remains deterministic, "
            "read-only, non-causal, and non-predictive"
        )
        print("[DONE] OI-043 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for item, original in backups.items():
            if original is None:
                if item.exists():
                    item.unlink()
            else:
                item.parent.mkdir(parents=True, exist_ok=True)
                item.write_bytes(original)

        print(
            "[ROLLBACK] OI-043 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
