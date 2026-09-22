from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-042"
INSTALLER_REVISION = "OI_042_ORACLE_REASONING_ASSEMBLY_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_036_oracle_reasoning_evidence_package.py", "OI-036"),
    (PACKAGE / "oi_039_reasoning_evidence_context_registry.py", "OI-039"),
    (PACKAGE / "oi_041_reasoning_evidence_relationship_registry.py", "OI-041"),
)

MODULE = PACKAGE / "oi_042_oracle_reasoning_assembly.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_042_oracle_reasoning_assembly.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_036_oracle_reasoning_evidence_package import (
    OracleReasoningEvidencePackage,
)
from .oi_039_reasoning_evidence_context_registry import (
    ReasoningEvidenceContextRegistry,
)
from .oi_041_reasoning_evidence_relationship_registry import (
    ReasoningEvidenceRelationshipRegistry,
)

BUILD_ID = "OI-042"
OI_042_REVISION = "OI_042_ORACLE_REASONING_ASSEMBLY_V1"

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


class OracleReasoningAssemblyError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class OracleReasoningAssembly:
    assembly_id: str
    query_id: str
    profile_id: str
    subject_hint: str
    admission_status: str
    evidence_package_hash: str
    context_registry_hash: str
    relationship_registry_hash: str
    evidence_count: int
    context_count: int
    relationship_count: int
    missing_need_count: int
    assembled_at: datetime
    assembly_hash: str
    read_only: bool
    predictive: bool
    causal_claim_allowed: bool


class OracleReasoningAssembler:
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

    def assemble(
        self,
        *,
        assembly_id: str,
        evidence_package: OracleReasoningEvidencePackage,
        context_registry: ReasoningEvidenceContextRegistry,
        relationship_registry: ReasoningEvidenceRelationshipRegistry,
        assembled_at: datetime,
    ) -> OracleReasoningAssembly:
        assembly_id_value = str(
            assembly_id
        ).strip()

        if not assembly_id_value:
            raise OracleReasoningAssemblyError(
                "assembly_id must not be empty"
            )

        if not isinstance(
            evidence_package,
            OracleReasoningEvidencePackage,
        ):
            raise TypeError(
                "evidence_package must be OracleReasoningEvidencePackage"
            )

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

        if (
            context_registry.package_hash
            != evidence_package.package_hash
        ):
            raise OracleReasoningAssemblyError(
                "context registry does not belong to evidence package"
            )

        if not isinstance(
            assembled_at,
            datetime,
        ):
            raise TypeError(
                "assembled_at must be datetime"
            )

        if assembled_at.tzinfo is None:
            raise OracleReasoningAssemblyError(
                "assembled_at must be timezone-aware"
            )

        assembled_at = assembled_at.astimezone(
            timezone.utc
        )

        body = {
            "assembly_id": assembly_id_value,
            "query_id": evidence_package.query_id,
            "profile_id": evidence_package.profile_id,
            "subject_hint": evidence_package.subject_hint,
            "admission_status": (
                evidence_package.admission_status
            ),
            "evidence_package_hash": (
                evidence_package.package_hash
            ),
            "context_registry_hash": (
                context_registry.registry_hash
            ),
            "relationship_registry_hash": (
                relationship_registry.registry_hash
            ),
            "evidence_count": len(
                evidence_package.evidence_items
            ),
            "context_count": len(
                context_registry.contexts
            ),
            "relationship_count": len(
                relationship_registry.relationships
            ),
            "missing_need_count": (
                evidence_package.missing_need_count
            ),
            "assembled_at": assembled_at,
            "read_only": True,
            "predictive": False,
            "causal_claim_allowed": False,
        }

        return OracleReasoningAssembly(
            assembly_id=assembly_id_value,
            query_id=evidence_package.query_id,
            profile_id=evidence_package.profile_id,
            subject_hint=evidence_package.subject_hint,
            admission_status=(
                evidence_package.admission_status
            ),
            evidence_package_hash=(
                evidence_package.package_hash
            ),
            context_registry_hash=(
                context_registry.registry_hash
            ),
            relationship_registry_hash=(
                relationship_registry.registry_hash
            ),
            evidence_count=len(
                evidence_package.evidence_items
            ),
            context_count=len(
                context_registry.contexts
            ),
            relationship_count=len(
                relationship_registry.relationships
            ),
            missing_need_count=(
                evidence_package.missing_need_count
            ),
            assembled_at=assembled_at,
            assembly_hash=deterministic_sha256(body),
            read_only=True,
            predictive=False,
            causal_claim_allowed=False,
        )


def verify_oracle_reasoning_assembly() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-042 must remain read-only"
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
            "OI-042 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_042_REVISION",
    "OracleReasoningAssemblyError",
    "OracleReasoningAssembly",
    "OracleReasoningAssembler",
    "verify_oracle_reasoning_assembly",
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
    OI_042_REVISION,
    OracleReasoningAssembler,
    verify_oracle_reasoning_assembly,
)

NOW = datetime(
    2026,
    8,
    11,
    5,
    0,
    tzinfo=timezone.utc,
)


def evidence_package():
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
    return ReasoningEvidenceContextRegistry(
        ReasoningEvidenceContextProjection(
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
                        "sports_context",
                    ),
                    context_hash="2" * 64,
                ),
            ),
            context_count=2,
            projection_hash="3" * 64,
            read_only=True,
        )
    )


def relationship_registry():
    return ReasoningEvidenceRelationshipRegistry(
        ReasoningEvidenceRelationshipProjection(
            evidence_registry_hash="4" * 64,
            context_registry_hash="5" * 64,
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
                    ),
                    relationship_hash="6" * 64,
                ),
            ),
            relationship_count=1,
            projection_hash="7" * 64,
            read_only=True,
        )
    )


class TestOI042(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oracle_reasoning_assembly()
        )

    def test_assembly(self):
        assembly = OracleReasoningAssembler().assemble(
            assembly_id="assembly.test",
            evidence_package=evidence_package(),
            context_registry=context_registry(),
            relationship_registry=relationship_registry(),
            assembled_at=NOW,
        )

        self.assertEqual(
            assembly.evidence_count,
            2,
        )
        self.assertEqual(
            assembly.context_count,
            2,
        )
        self.assertEqual(
            assembly.relationship_count,
            1,
        )

    def test_lineage(self):
        assembly = OracleReasoningAssembler().assemble(
            assembly_id="assembly.test",
            evidence_package=evidence_package(),
            context_registry=context_registry(),
            relationship_registry=relationship_registry(),
            assembled_at=NOW,
        )

        self.assertEqual(
            assembly.evidence_package_hash,
            "e" * 64,
        )

    def test_non_causal(self):
        assembly = OracleReasoningAssembler().assemble(
            assembly_id="assembly.test",
            evidence_package=evidence_package(),
            context_registry=context_registry(),
            relationship_registry=relationship_registry(),
            assembled_at=NOW,
        )

        self.assertFalse(
            assembly.predictive
        )
        self.assertFalse(
            assembly.causal_claim_allowed
        )
        self.assertTrue(
            assembly.read_only
        )

    def test_deterministic(self):
        assembler = OracleReasoningAssembler()

        a = assembler.assemble(
            assembly_id="assembly.test",
            evidence_package=evidence_package(),
            context_registry=context_registry(),
            relationship_registry=relationship_registry(),
            assembled_at=NOW,
        )

        b = assembler.assemble(
            assembly_id="assembly.test",
            evidence_package=evidence_package(),
            context_registry=context_registry(),
            relationship_registry=relationship_registry(),
            assembled_at=NOW,
        )

        self.assertEqual(
            a.assembly_hash,
            b.assembly_hash,
        )

    def test_side_effects(self):
        assembler = OracleReasoningAssembler()

        self.assertTrue(assembler.read_only)
        self.assertFalse(assembler.network_allowed)
        self.assertFalse(assembler.persistence_allowed)
        self.assertFalse(assembler.publication_allowed)
        self.assertFalse(assembler.execution_allowed)
        self.assertFalse(assembler.qseries_execution_allowed)
        self.assertFalse(assembler.prediction_allowed)
        self.assertFalse(assembler.edge_score_allowed)
        self.assertFalse(assembler.probability_allowed)
        self.assertFalse(assembler.causal_claim_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-042 CERTIFICATION TEST")
    print(" ORACLE REASONING ASSEMBLY")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI042
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-042")
    print(f"[PASS] Revision: {OI_042_REVISION}")
    print("[PASS] Evidence, context, and structural relationships assembled for Oracle reasoning")
    print("[PASS] Evidence lineage, context lineage, relationship lineage, and admission status preserved")
    print("[PASS] Assembly remains read-only, non-causal, non-predictive, and non-scoring")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-042 CERTIFIED")
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
    print(" OI-042 INSTALLER")
    print(" ORACLE REASONING ASSEMBLY")
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
        "[PASS] Certified OI-036, OI-039, "
        "and OI-041 verified read-only"
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
            "from .oi_042_oracle_reasoning_assembly import *"
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
            "[PASS] Oracle reasoning assembly remains deterministic, "
            "read-only, structural, and non-causal"
        )
        print("[DONE] OI-042 INSTALLATION COMPLETE")
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
            "[ROLLBACK] OI-042 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
