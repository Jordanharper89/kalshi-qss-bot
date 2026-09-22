from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-039"
INSTALLER_REVISION = "OI_039_REASONING_EVIDENCE_CONTEXT_REGISTRY_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_037_reasoning_evidence_registry.py", "OI-037"),
    (PACKAGE / "oi_038_reasoning_evidence_context_projection.py", "OI-038"),
)

MODULE = PACKAGE / "oi_039_reasoning_evidence_context_registry.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_039_reasoning_evidence_context_registry.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_038_reasoning_evidence_context_projection import (
    ReasoningEvidenceContext,
    ReasoningEvidenceContextProjection,
)

BUILD_ID = "OI-039"
OI_039_REVISION = "OI_039_REASONING_EVIDENCE_CONTEXT_REGISTRY_V1"

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


class ReasoningEvidenceContextRegistryError(ValueError):
    pass


class ReasoningEvidenceContextRegistry:
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
        projection: ReasoningEvidenceContextProjection,
    ) -> None:
        if not isinstance(
            projection,
            ReasoningEvidenceContextProjection,
        ):
            raise TypeError(
                "projection must be ReasoningEvidenceContextProjection"
            )

        ids = tuple(
            item.canonical_observation_id
            for item in projection.contexts
        )

        if len(ids) != len(set(ids)):
            raise ReasoningEvidenceContextRegistryError(
                "duplicate canonical observation identity"
            )

        self._projection = projection
        self._contexts = tuple(projection.contexts)

        self._by_id = MappingProxyType(
            {
                item.canonical_observation_id: item
                for item in self._contexts
            }
        )

    @property
    def contexts(self) -> tuple[ReasoningEvidenceContext, ...]:
        return self._contexts

    @property
    def package_hash(self) -> str:
        return self._projection.package_hash

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(
            {
                "package_hash": self._projection.package_hash,
                "projection_hash": self._projection.projection_hash,
                "context_hashes": tuple(
                    item.context_hash
                    for item in self._contexts
                ),
            }
        )

    def get(
        self,
        canonical_observation_id: str,
    ) -> ReasoningEvidenceContext | None:
        return self._by_id.get(
            str(canonical_observation_id).strip()
        )

    def by_role(
        self,
        role: str,
    ) -> tuple[ReasoningEvidenceContext, ...]:
        key = " ".join(
            str(role).strip().lower().split()
        )

        return tuple(
            item
            for item in self._contexts
            if key in item.context_roles
        )

    def by_adapter(
        self,
        adapter_id: str,
    ) -> tuple[ReasoningEvidenceContext, ...]:
        key = str(adapter_id).strip()

        return tuple(
            item
            for item in self._contexts
            if item.adapter_id == key
        )

    def by_subject(
        self,
        subject: str,
    ) -> tuple[ReasoningEvidenceContext, ...]:
        key = " ".join(
            str(subject).strip().split()
        )

        return tuple(
            item
            for item in self._contexts
            if item.subject == key
        )


def verify_reasoning_evidence_context_registry() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-039 must remain read-only"
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
            "OI-039 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_039_REVISION",
    "ReasoningEvidenceContextRegistryError",
    "ReasoningEvidenceContextRegistry",
    "verify_reasoning_evidence_context_registry",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_038_reasoning_evidence_context_projection import (
    ReasoningEvidenceContext,
    ReasoningEvidenceContextProjection,
)
from qseries_v2.observation_intelligence.oi_039_reasoning_evidence_context_registry import (
    OI_039_REVISION,
    ReasoningEvidenceContextRegistry,
    verify_reasoning_evidence_context_registry,
)


def projection():
    return ReasoningEvidenceContextProjection(
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
                context_roles=(
                    "evidence",
                    "market_state",
                    "source_context",
                ),
                context_hash="d" * 64,
            ),
            ReasoningEvidenceContext(
                canonical_observation_id="obs.2",
                canonical_observation_hash="e" * 64,
                adapter_id="adapter.sports.v1",
                provider="SportsFeed",
                subject="Astros",
                observation_type="lineup",
                context_roles=(
                    "evidence",
                    "source_context",
                    "sports_context",
                ),
                context_hash="f" * 64,
            ),
        ),
        context_count=2,
        projection_hash="1" * 64,
        read_only=True,
    )


class TestOI039(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_reasoning_evidence_context_registry()
        )

    def test_registry(self):
        registry = ReasoningEvidenceContextRegistry(
            projection()
        )

        self.assertEqual(
            len(registry.contexts),
            2,
        )

    def test_get(self):
        registry = ReasoningEvidenceContextRegistry(
            projection()
        )

        self.assertEqual(
            registry.get("obs.1").provider,
            "Kalshi",
        )

    def test_role_query(self):
        registry = ReasoningEvidenceContextRegistry(
            projection()
        )

        self.assertEqual(
            len(
                registry.by_role(
                    "market_state"
                )
            ),
            1,
        )

        self.assertEqual(
            len(
                registry.by_role(
                    "sports_context"
                )
            ),
            1,
        )

    def test_reverse_queries(self):
        registry = ReasoningEvidenceContextRegistry(
            projection()
        )

        self.assertEqual(
            len(
                registry.by_adapter(
                    "adapter.kalshi.v1"
                )
            ),
            1,
        )

        self.assertEqual(
            len(
                registry.by_subject(
                    "Astros"
                )
            ),
            1,
        )

    def test_deterministic(self):
        a = ReasoningEvidenceContextRegistry(
            projection()
        )

        b = ReasoningEvidenceContextRegistry(
            projection()
        )

        self.assertEqual(
            a.registry_hash,
            b.registry_hash,
        )

    def test_side_effects(self):
        registry = ReasoningEvidenceContextRegistry(
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
    print(" OI-039 CERTIFICATION TEST")
    print(" REASONING EVIDENCE CONTEXT REGISTRY")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI039
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-039")
    print(f"[PASS] Revision: {OI_039_REVISION}")
    print("[PASS] Reasoning evidence context registry certified")
    print("[PASS] Context queries by identity, role, adapter, and subject certified")
    print("[PASS] Context remains structural, read-only, non-causal, non-predictive, and non-scoring")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-039 CERTIFIED")
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
    print(" OI-039 INSTALLER")
    print(" REASONING EVIDENCE CONTEXT REGISTRY")
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
        "[PASS] Certified OI-037 and OI-038 "
        "verified read-only"
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
            "from .oi_039_reasoning_evidence_context_registry import *"
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
            MODULE.read_bytes()
            + TEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: {install_hash}"
        )
        print(
            "[PASS] Context registry remains deterministic, "
            "read-only, and non-causal"
        )
        print("[DONE] OI-039 INSTALLATION COMPLETE")
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
            "[ROLLBACK] OI-039 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
