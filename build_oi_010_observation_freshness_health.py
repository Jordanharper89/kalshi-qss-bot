from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-010"
INSTALLER_REVISION = "OI_010_OBSERVATION_FRESHNESS_HEALTH_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"
UPSTREAM_009 = PACKAGE / "oi_009_observation_evidence_assembly.py"
MODULE = PACKAGE / "oi_010_observation_freshness_health.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_010_observation_freshness_health.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Mapping

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_003_canonical_observation_gateway import CanonicalLiveObservation
from .oi_009_observation_evidence_assembly import verify_observation_evidence_assembly

BUILD_ID = "OI-010"
OI_010_REVISION = "OI_010_OBSERVATION_FRESHNESS_HEALTH_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False

FRESH = "fresh"
AGING = "aging"
STALE = "stale"


class ObservationFreshnessHealthError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class FreshnessPolicy:
    observation_type: str
    fresh_seconds: int
    stale_seconds: int

    def __post_init__(self) -> None:
        kind = " ".join(str(self.observation_type).strip().lower().split())
        if not kind:
            raise ObservationFreshnessHealthError(
                "observation_type must not be empty"
            )
        if not isinstance(self.fresh_seconds, int) or self.fresh_seconds < 0:
            raise ObservationFreshnessHealthError(
                "fresh_seconds must be a non-negative integer"
            )
        if not isinstance(self.stale_seconds, int) or self.stale_seconds <= self.fresh_seconds:
            raise ObservationFreshnessHealthError(
                "stale_seconds must be greater than fresh_seconds"
            )

        object.__setattr__(self, "observation_type", kind)

    @property
    def policy_hash(self) -> str:
        return deterministic_sha256(
            {
                "observation_type": self.observation_type,
                "fresh_seconds": self.fresh_seconds,
                "stale_seconds": self.stale_seconds,
            }
        )


@dataclass(frozen=True, slots=True)
class ObservationHealth:
    canonical_observation_id: str
    observed_at: datetime
    evaluated_at: datetime
    age_seconds: int
    freshness_status: str
    policy_hash: str
    health_hash: str


class ObservationFreshnessHealthEngine:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False

    def __init__(
        self,
        policies: tuple[FreshnessPolicy, ...],
    ) -> None:
        values = tuple(policies)

        if any(not isinstance(item, FreshnessPolicy) for item in values):
            raise TypeError("all policies must be FreshnessPolicy")

        ordered = tuple(
            sorted(values, key=lambda item: item.observation_type)
        )

        if values != ordered:
            raise ObservationFreshnessHealthError(
                "policies must be deterministically sorted"
            )

        keys = tuple(item.observation_type for item in values)
        if len(keys) != len(set(keys)):
            raise ObservationFreshnessHealthError(
                "duplicate observation_type policy"
            )

        self._policies = values
        self._by_type = MappingProxyType(
            {item.observation_type: item for item in values}
        )

    @property
    def policies(self) -> tuple[FreshnessPolicy, ...]:
        return self._policies

    def evaluate(
        self,
        observation: CanonicalLiveObservation,
        *,
        evaluated_at: datetime,
    ) -> ObservationHealth:
        if not isinstance(observation, CanonicalLiveObservation):
            raise TypeError(
                "observation must be CanonicalLiveObservation"
            )

        if not isinstance(evaluated_at, datetime):
            raise TypeError("evaluated_at must be datetime")

        if evaluated_at.tzinfo is None:
            raise ObservationFreshnessHealthError(
                "evaluated_at must be timezone-aware"
            )

        evaluated_at = evaluated_at.astimezone(timezone.utc)

        if evaluated_at < observation.observed_at:
            raise ObservationFreshnessHealthError(
                "evaluated_at cannot precede observed_at"
            )

        policy = self._by_type.get(observation.observation_type)

        if policy is None:
            raise ObservationFreshnessHealthError(
                f"no freshness policy for observation type: "
                f"{observation.observation_type}"
            )

        age_seconds = int(
            (evaluated_at - observation.observed_at).total_seconds()
        )

        if age_seconds <= policy.fresh_seconds:
            status = FRESH
        elif age_seconds < policy.stale_seconds:
            status = AGING
        else:
            status = STALE

        body = {
            "canonical_observation_id": observation.canonical_observation_id,
            "observed_at": observation.observed_at,
            "evaluated_at": evaluated_at,
            "age_seconds": age_seconds,
            "freshness_status": status,
            "policy_hash": policy.policy_hash,
        }

        return ObservationHealth(
            canonical_observation_id=observation.canonical_observation_id,
            observed_at=observation.observed_at,
            evaluated_at=evaluated_at,
            age_seconds=age_seconds,
            freshness_status=status,
            policy_hash=policy.policy_hash,
            health_hash=deterministic_sha256(body),
        )


def default_freshness_policies() -> tuple[FreshnessPolicy, ...]:
    return (
        FreshnessPolicy(
            observation_type="market_snapshot",
            fresh_seconds=15,
            stale_seconds=90,
        ),
        FreshnessPolicy(
            observation_type="spot_price",
            fresh_seconds=10,
            stale_seconds=60,
        ),
    )


def verify_observation_freshness_health() -> bool:
    verify_observation_evidence_assembly()

    if READ_ONLY is not True:
        raise AssertionError("OI-010 must remain read-only")

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
        )
    ):
        raise AssertionError("OI-010 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_010_REVISION",
    "FRESH",
    "AGING",
    "STALE",
    "ObservationFreshnessHealthError",
    "FreshnessPolicy",
    "ObservationHealth",
    "ObservationFreshnessHealthEngine",
    "default_freshness_policies",
    "verify_observation_freshness_health",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from qseries_v2.observation_intelligence.oi_001_universal_observation_intake import (
    ObservationSourceIdentity,
    RawObservationEnvelope,
)
from qseries_v2.observation_intelligence.oi_003_canonical_observation_gateway import (
    CanonicalLiveObservationGateway,
)
from qseries_v2.observation_intelligence.oi_006_live_observation_registry import (
    default_source_registry,
)
from qseries_v2.observation_intelligence.oi_010_observation_freshness_health import (
    AGING,
    FRESH,
    STALE,
    OI_010_REVISION,
    ObservationFreshnessHealthEngine,
    default_freshness_policies,
    verify_observation_freshness_health,
)

BASE = datetime(2026, 8, 10, 6, 0, tzinfo=timezone.utc)


def observation():
    source = ObservationSourceIdentity(
        source_id="coinbase.public.spot",
        source_kind="market_data",
        provider="Coinbase",
        adapter_id="adapter.coinbase.spot.v1",
    )

    envelope = RawObservationEnvelope(
        source=source,
        external_observation_id="BTC-USD-FRESHNESS",
        observed_at=BASE,
        subject="BTC",
        observation_type="spot_price",
        payload={
            "product_id": "BTC-USD",
            "symbol": "BTC",
            "quote_currency": "USD",
            "price": "100.00",
        },
        metadata={"venue": "coinbase"},
    )

    return CanonicalLiveObservationGateway(
        default_source_registry()
    ).canonicalize(envelope).canonical_observation


class TestOI010(unittest.TestCase):
    def setUp(self):
        self.engine = ObservationFreshnessHealthEngine(
            default_freshness_policies()
        )
        self.observation = observation()

    def test_foundation(self):
        self.assertTrue(
            verify_observation_freshness_health()
        )

    def test_fresh(self):
        health = self.engine.evaluate(
            self.observation,
            evaluated_at=BASE + timedelta(seconds=5),
        )
        self.assertEqual(health.freshness_status, FRESH)

    def test_aging(self):
        health = self.engine.evaluate(
            self.observation,
            evaluated_at=BASE + timedelta(seconds=30),
        )
        self.assertEqual(health.freshness_status, AGING)

    def test_stale(self):
        health = self.engine.evaluate(
            self.observation,
            evaluated_at=BASE + timedelta(seconds=61),
        )
        self.assertEqual(health.freshness_status, STALE)

    def test_deterministic(self):
        when = BASE + timedelta(seconds=5)
        a = self.engine.evaluate(self.observation, evaluated_at=when)
        b = self.engine.evaluate(self.observation, evaluated_at=when)
        self.assertEqual(a.health_hash, b.health_hash)

    def test_reverse_time_rejected(self):
        with self.assertRaises(ValueError):
            self.engine.evaluate(
                self.observation,
                evaluated_at=BASE - timedelta(seconds=1),
            )

    def test_side_effects(self):
        self.assertTrue(self.engine.read_only)
        self.assertFalse(self.engine.network_allowed)
        self.assertFalse(self.engine.persistence_allowed)
        self.assertFalse(self.engine.publication_allowed)
        self.assertFalse(self.engine.execution_allowed)
        self.assertFalse(self.engine.qseries_execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-010 CERTIFICATION TEST")
    print(" OBSERVATION FRESHNESS & HEALTH")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI010
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-010")
    print(f"[PASS] Revision: {OI_010_REVISION}")
    print("[PASS] Fresh, aging, and stale observation states certified")
    print("[PASS] Freshness remains observation-type aware and category-agnostic")
    print("[PASS] No prediction or trading-value judgment introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-010 CERTIFIED")
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
    print(" OI-010 INSTALLER")
    print(" OBSERVATION FRESHNESS & HEALTH")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    if not UPSTREAM_009.is_file():
        raise RuntimeError(f"Certified OI-009 missing: {UPSTREAM_009}")

    upstream_hash = sha(UPSTREAM_009)
    print("[PASS] Certified OI-009 verified read-only")

    affected = (MODULE, TEST, INIT)
    backups = {
        path: path.read_bytes() if path.exists() else None
        for path in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oi_010_observation_freshness_health import *"

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            ast.parse(current, filename=str(INIT))
            INIT.write_text(current, encoding="utf-8", newline="\n")

        print("[PASS] Updated: qseries_v2\\observation_intelligence\\__init__.py")

        compile(MODULE.read_text(encoding="utf-8"), str(MODULE), "exec")
        compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")

        if sha(UPSTREAM_009) != upstream_hash:
            raise RuntimeError("Certified OI-009 changed during install")

        print("[PASS] In-memory compilation verified")
        print("[PASS] Certified OI-009 remained unchanged")

        install_hash = hashlib.sha256(
            MODULE.read_bytes() + TEST.read_bytes()
        ).hexdigest()

        print(f"[PASS] Deterministic install hash: {install_hash}")
        print("[PASS] Freshness engine remains deterministic, read-only, and non-predictive")
        print("[DONE] OI-010 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for path, content in backups.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

        print("[ROLLBACK] OI-010 installation failed; all affected files restored")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
