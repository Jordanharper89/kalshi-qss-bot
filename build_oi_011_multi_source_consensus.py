from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-011"
INSTALLER_REVISION = "OI_011_MULTI_SOURCE_CONSENSUS_FOUNDATION_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"
UPSTREAM_010 = PACKAGE / "oi_010_observation_freshness_health.py"
MODULE = PACKAGE / "oi_011_multi_source_consensus.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_011_multi_source_consensus.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from statistics import median

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_003_canonical_observation_gateway import CanonicalLiveObservation
from .oi_010_observation_freshness_health import (
    FRESH,
    ObservationHealth,
    verify_observation_freshness_health,
)

BUILD_ID = "OI-011"
OI_011_REVISION = "OI_011_MULTI_SOURCE_CONSENSUS_FOUNDATION_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False


class MultiSourceConsensusError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SourceConsensusMember:
    canonical_observation_id: str
    source_id: str
    provider: str
    adapter_id: str
    observed_at: datetime
    value: float
    freshness_status: str


@dataclass(frozen=True, slots=True)
class MultiSourceConsensus:
    subject: str
    observation_type: str
    members: tuple[SourceConsensusMember, ...]
    fresh_member_count: int
    source_count: int
    median_value: float
    min_value: float
    max_value: float
    spread_ratio: float
    consensus_hash: str


class MultiSourceConsensusEngine:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False

    def build_numeric_consensus(
        self,
        *,
        observations: tuple[CanonicalLiveObservation, ...],
        health: tuple[ObservationHealth, ...],
        value_field: str,
    ) -> MultiSourceConsensus:
        values = tuple(observations)
        health_values = tuple(health)

        if not values:
            raise MultiSourceConsensusError(
                "at least one observation is required"
            )

        if len(values) != len(health_values):
            raise MultiSourceConsensusError(
                "observation and health counts must match"
            )

        ordered = tuple(
            sorted(
                values,
                key=lambda item: (
                    item.source_id,
                    item.canonical_observation_id,
                ),
            )
        )

        if values != ordered:
            raise MultiSourceConsensusError(
                "observations must be deterministically sorted by source"
            )

        health_by_id = {
            item.canonical_observation_id: item
            for item in health_values
        }

        if len(health_by_id) != len(health_values):
            raise MultiSourceConsensusError(
                "duplicate health observation identity"
            )

        subjects = {item.subject for item in values}
        types = {item.observation_type for item in values}

        if len(subjects) != 1 or len(types) != 1:
            raise MultiSourceConsensusError(
                "consensus observations must share subject and observation_type"
            )

        members = []

        for item in values:
            health_item = health_by_id.get(
                item.canonical_observation_id
            )

            if health_item is None:
                raise MultiSourceConsensusError(
                    "missing health record for observation"
                )

            raw = item.facts.get(value_field)

            try:
                numeric = float(raw)
            except (TypeError, ValueError) as exc:
                raise MultiSourceConsensusError(
                    f"non-numeric consensus field: {value_field}"
                ) from exc

            members.append(
                SourceConsensusMember(
                    canonical_observation_id=item.canonical_observation_id,
                    source_id=item.source_id,
                    provider=item.provider,
                    adapter_id=item.adapter_id,
                    observed_at=item.observed_at,
                    value=numeric,
                    freshness_status=health_item.freshness_status,
                )
            )

        numeric_values = tuple(item.value for item in members)
        middle = float(median(numeric_values))
        low = min(numeric_values)
        high = max(numeric_values)
        spread_ratio = 0.0 if middle == 0 else (high - low) / abs(middle)

        body = {
            "subject": values[0].subject,
            "observation_type": values[0].observation_type,
            "member_ids": tuple(
                item.canonical_observation_id
                for item in members
            ),
            "values": numeric_values,
            "freshness": tuple(
                item.freshness_status
                for item in members
            ),
            "median_value": middle,
            "min_value": low,
            "max_value": high,
            "spread_ratio": spread_ratio,
        }

        return MultiSourceConsensus(
            subject=values[0].subject,
            observation_type=values[0].observation_type,
            members=tuple(members),
            fresh_member_count=sum(
                1
                for item in members
                if item.freshness_status == FRESH
            ),
            source_count=len(
                {item.source_id for item in members}
            ),
            median_value=middle,
            min_value=low,
            max_value=high,
            spread_ratio=spread_ratio,
            consensus_hash=deterministic_sha256(body),
        )


def verify_multi_source_consensus() -> bool:
    verify_observation_freshness_health()

    if READ_ONLY is not True:
        raise AssertionError("OI-011 must remain read-only")

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
        )
    ):
        raise AssertionError("OI-011 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_011_REVISION",
    "MultiSourceConsensusError",
    "SourceConsensusMember",
    "MultiSourceConsensus",
    "MultiSourceConsensusEngine",
    "verify_multi_source_consensus",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_001_universal_observation_intake import (
    ObservationSourceIdentity,
    RawObservationEnvelope,
)
from qseries_v2.observation_intelligence.oi_002_source_adapter_registry import (
    SourceAdapterDescriptor,
    SourceAdapterRegistry,
)
from qseries_v2.observation_intelligence.oi_003_canonical_observation_gateway import (
    CanonicalLiveObservationGateway,
)
from qseries_v2.observation_intelligence.oi_010_observation_freshness_health import (
    ObservationFreshnessHealthEngine,
    default_freshness_policies,
)
from qseries_v2.observation_intelligence.oi_011_multi_source_consensus import (
    OI_011_REVISION,
    MultiSourceConsensusEngine,
    verify_multi_source_consensus,
)

NOW = datetime(2026, 8, 10, 7, 0, tzinfo=timezone.utc)


def registry():
    return SourceAdapterRegistry(
        (
            SourceAdapterDescriptor(
                adapter_id="adapter.exchange.a",
                source_id="exchange.a",
                source_kind="market_data",
                provider="Exchange A",
                adapter_version="1",
                capabilities=("spot price",),
                enabled_for_intake=True,
            ),
            SourceAdapterDescriptor(
                adapter_id="adapter.exchange.b",
                source_id="exchange.b",
                source_kind="market_data",
                provider="Exchange B",
                adapter_version="1",
                capabilities=("spot price",),
                enabled_for_intake=True,
            ),
        )
    )


def observation(source_id, provider, adapter_id, external_id, price):
    envelope = RawObservationEnvelope(
        source=ObservationSourceIdentity(
            source_id=source_id,
            source_kind="market_data",
            provider=provider,
            adapter_id=adapter_id,
        ),
        external_observation_id=external_id,
        observed_at=NOW,
        subject="BTC",
        observation_type="spot_price",
        payload={
            "symbol": "BTC",
            "quote_currency": "USD",
            "price": price,
        },
        metadata={},
    )

    return CanonicalLiveObservationGateway(
        registry()
    ).canonicalize(envelope).canonical_observation


class TestOI011(unittest.TestCase):
    def setUp(self):
        self.a = observation(
            "exchange.a",
            "Exchange A",
            "adapter.exchange.a",
            "a",
            "100.0",
        )
        self.b = observation(
            "exchange.b",
            "Exchange B",
            "adapter.exchange.b",
            "b",
            "102.0",
        )

        self.values = tuple(
            sorted(
                (self.a, self.b),
                key=lambda item: (
                    item.source_id,
                    item.canonical_observation_id,
                ),
            )
        )

        health_engine = ObservationFreshnessHealthEngine(
            default_freshness_policies()
        )

        self.health = tuple(
            health_engine.evaluate(
                item,
                evaluated_at=NOW,
            )
            for item in self.values
        )

    def test_foundation(self):
        self.assertTrue(verify_multi_source_consensus())

    def test_consensus(self):
        result = MultiSourceConsensusEngine().build_numeric_consensus(
            observations=self.values,
            health=self.health,
            value_field="price",
        )

        self.assertEqual(result.source_count, 2)
        self.assertEqual(result.fresh_member_count, 2)
        self.assertEqual(result.median_value, 101.0)

    def test_range(self):
        result = MultiSourceConsensusEngine().build_numeric_consensus(
            observations=self.values,
            health=self.health,
            value_field="price",
        )

        self.assertEqual(result.min_value, 100.0)
        self.assertEqual(result.max_value, 102.0)

    def test_deterministic(self):
        engine = MultiSourceConsensusEngine()
        a = engine.build_numeric_consensus(
            observations=self.values,
            health=self.health,
            value_field="price",
        )
        b = engine.build_numeric_consensus(
            observations=self.values,
            health=self.health,
            value_field="price",
        )
        self.assertEqual(a.consensus_hash, b.consensus_hash)

    def test_side_effects(self):
        engine = MultiSourceConsensusEngine()
        self.assertTrue(engine.read_only)
        self.assertFalse(engine.network_allowed)
        self.assertFalse(engine.persistence_allowed)
        self.assertFalse(engine.publication_allowed)
        self.assertFalse(engine.execution_allowed)
        self.assertFalse(engine.qseries_execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-011 CERTIFICATION TEST")
    print(" MULTI-SOURCE CONSENSUS FOUNDATION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI011
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-011")
    print(f"[PASS] Revision: {OI_011_REVISION}")
    print("[PASS] Multi-source numeric observation consensus certified")
    print("[PASS] Source count, freshness count, median, range, and spread certified")
    print("[PASS] Consensus remains descriptive and non-predictive")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-011 CERTIFIED")
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
    print(" OI-011 INSTALLER")
    print(" MULTI-SOURCE CONSENSUS FOUNDATION")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    if not UPSTREAM_010.is_file():
        raise RuntimeError(f"Certified OI-010 missing: {UPSTREAM_010}")

    upstream_hash = sha(UPSTREAM_010)
    print("[PASS] Certified OI-010 verified read-only")

    affected = (MODULE, TEST, INIT)
    backups = {
        path: path.read_bytes() if path.exists() else None
        for path in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oi_011_multi_source_consensus import *"

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            ast.parse(current, filename=str(INIT))
            INIT.write_text(current, encoding="utf-8", newline="\n")

        print("[PASS] Updated: qseries_v2\\observation_intelligence\\__init__.py")

        compile(MODULE.read_text(encoding="utf-8"), str(MODULE), "exec")
        compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")

        if sha(UPSTREAM_010) != upstream_hash:
            raise RuntimeError("Certified OI-010 changed during install")

        print("[PASS] In-memory compilation verified")
        print("[PASS] Certified OI-010 remained unchanged")

        install_hash = hashlib.sha256(
            MODULE.read_bytes() + TEST.read_bytes()
        ).hexdigest()

        print(f"[PASS] Deterministic install hash: {install_hash}")
        print("[PASS] Consensus foundation remains deterministic, read-only, and non-predictive")
        print("[DONE] OI-011 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for path, content in backups.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

        print("[ROLLBACK] OI-011 installation failed; all affected files restored")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
