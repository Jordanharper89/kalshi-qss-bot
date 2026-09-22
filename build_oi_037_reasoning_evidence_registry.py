from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-037"
INSTALLER_REVISION = "OI_037_REASONING_EVIDENCE_REGISTRY_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_034_canonical_evidence_materialization.py", "OI-034"),
    (PACKAGE / "oi_035_reasoning_evidence_admission_gate.py", "OI-035"),
    (PACKAGE / "oi_036_oracle_reasoning_evidence_package.py", "OI-036"),
)

MODULE = PACKAGE / "oi_037_reasoning_evidence_registry.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_037_reasoning_evidence_registry.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_036_oracle_reasoning_evidence_package import (
    OracleReasoningEvidenceItem,
    OracleReasoningEvidencePackage,
)

BUILD_ID = "OI-037"
OI_037_REVISION = "OI_037_REASONING_EVIDENCE_REGISTRY_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False


class ReasoningEvidenceRegistryError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ReasoningEvidenceRegistryRecord:
    canonical_observation_id: str
    canonical_observation_hash: str
    adapter_id: str
    provider: str
    subject: str
    observation_type: str


class ReasoningEvidenceRegistry:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False

    def __init__(
        self,
        package: OracleReasoningEvidencePackage,
    ) -> None:
        if not isinstance(
            package,
            OracleReasoningEvidencePackage,
        ):
            raise TypeError(
                "package must be OracleReasoningEvidencePackage"
            )

        records = tuple(
            ReasoningEvidenceRegistryRecord(
                canonical_observation_id=item.canonical_observation_id,
                canonical_observation_hash=item.canonical_observation_hash,
                adapter_id=item.adapter_id,
                provider=item.provider,
                subject=item.subject,
                observation_type=item.observation_type,
            )
            for item in package.evidence_items
        )

        ordered = tuple(
            sorted(
                records,
                key=lambda item: item.canonical_observation_id,
            )
        )

        ids = tuple(
            item.canonical_observation_id
            for item in ordered
        )

        if len(ids) != len(set(ids)):
            raise ReasoningEvidenceRegistryError(
                "duplicate canonical observation identity"
            )

        self._package = package
        self._records = ordered
        self._by_id = MappingProxyType(
            {
                item.canonical_observation_id: item
                for item in ordered
            }
        )

    @property
    def package_hash(self) -> str:
        return self._package.package_hash

    @property
    def records(self) -> tuple[ReasoningEvidenceRegistryRecord, ...]:
        return self._records

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(
            {
                "package_hash": self._package.package_hash,
                "record_ids": tuple(
                    item.canonical_observation_id
                    for item in self._records
                ),
                "record_hashes": tuple(
                    item.canonical_observation_hash
                    for item in self._records
                ),
            }
        )

    def get(
        self,
        canonical_observation_id: str,
    ) -> ReasoningEvidenceRegistryRecord | None:
        key = str(canonical_observation_id).strip()
        return self._by_id.get(key)

    def by_adapter(
        self,
        adapter_id: str,
    ) -> tuple[ReasoningEvidenceRegistryRecord, ...]:
        key = str(adapter_id).strip()
        return tuple(
            item
            for item in self._records
            if item.adapter_id == key
        )

    def by_provider(
        self,
        provider: str,
    ) -> tuple[ReasoningEvidenceRegistryRecord, ...]:
        key = " ".join(str(provider).strip().split())
        return tuple(
            item
            for item in self._records
            if item.provider == key
        )

    def by_subject(
        self,
        subject: str,
    ) -> tuple[ReasoningEvidenceRegistryRecord, ...]:
        key = " ".join(str(subject).strip().split())
        return tuple(
            item
            for item in self._records
            if item.subject == key
        )

    def by_observation_type(
        self,
        observation_type: str,
    ) -> tuple[ReasoningEvidenceRegistryRecord, ...]:
        key = " ".join(
            str(observation_type).strip().lower().split()
        )
        return tuple(
            item
            for item in self._records
            if item.observation_type == key
        )


def verify_reasoning_evidence_registry() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-037 must remain read-only"
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
            "OI-037 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_037_REVISION",
    "ReasoningEvidenceRegistryError",
    "ReasoningEvidenceRegistryRecord",
    "ReasoningEvidenceRegistry",
    "verify_reasoning_evidence_registry",
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
    OI_037_REVISION,
    ReasoningEvidenceRegistry,
    verify_reasoning_evidence_registry,
)

NOW = datetime(
    2026,
    8,
    11,
    2,
    0,
    tzinfo=timezone.utc,
)


def package():
    return OracleReasoningEvidencePackage(
        package_id="reasoning.astros",
        query_id="query.astros",
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
                adapter_id="adapter.kalshi.v1",
                provider="Kalshi",
                subject="Astros strikeouts",
                observation_type="market_snapshot",
                observed_at=NOW,
            ),
        ),
        missing_need_count=0,
        built_at=NOW,
        package_hash="e" * 64,
        read_only=True,
        predictive=False,
    )


class TestOI037(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_reasoning_evidence_registry()
        )

    def test_registry(self):
        registry = ReasoningEvidenceRegistry(
            package()
        )

        self.assertEqual(
            len(registry.records),
            2,
        )

    def test_get(self):
        registry = ReasoningEvidenceRegistry(
            package()
        )

        self.assertEqual(
            registry.get("obs.1").adapter_id,
            "adapter.kalshi.v1",
        )

    def test_reverse_queries(self):
        registry = ReasoningEvidenceRegistry(
            package()
        )

        self.assertEqual(
            len(
                registry.by_adapter(
                    "adapter.kalshi.v1"
                )
            ),
            2,
        )

        self.assertEqual(
            len(
                registry.by_subject(
                    "Astros strikeouts"
                )
            ),
            2,
        )

        self.assertEqual(
            len(
                registry.by_observation_type(
                    "market_snapshot"
                )
            ),
            2,
        )

    def test_unknown(self):
        registry = ReasoningEvidenceRegistry(
            package()
        )

        self.assertIsNone(
            registry.get("obs.unknown")
        )

        self.assertEqual(
            registry.by_provider("Unknown"),
            (),
        )

    def test_deterministic(self):
        a = ReasoningEvidenceRegistry(
            package()
        )

        b = ReasoningEvidenceRegistry(
            package()
        )

        self.assertEqual(
            a.registry_hash,
            b.registry_hash,
        )

    def test_side_effects(self):
        registry = ReasoningEvidenceRegistry(
            package()
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


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-037 CERTIFICATION TEST")
    print(" REASONING EVIDENCE REGISTRY")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI037
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-037")
    print(f"[PASS] Revision: {OI_037_REVISION}")
    print("[PASS] Reasoning-ready canonical evidence registry certified")
    print("[PASS] Evidence queries by identity, adapter, provider, subject, and observation type certified")
    print("[PASS] Registry remains deterministic, read-only, non-predictive, and non-scoring")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-037 CERTIFIED")
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
    print(" OI-037 INSTALLER")
    print(" REASONING EVIDENCE REGISTRY")
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
        "[PASS] Certified OI-034 through OI-036 "
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
            "from .oi_037_reasoning_evidence_registry import *"
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
            "[PASS] Reasoning evidence registry remains "
            "deterministic, read-only, and fail-closed"
        )

        print(
            "[DONE] OI-037 INSTALLATION COMPLETE"
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
            "[ROLLBACK] OI-037 installation failed; "
            "all affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
